from collections import Counter

from app.parsers.bin_codec import char_to_soft_bin, soft_bin_to_char
from app.schemas.parsing import (
    ParseResult,
    ParseStatus,
    SourceBinDefinition,
    SourceFormat,
    SourceParseResult,
    ValidationIssue,
    ValidationSeverity,
    ValidationStage,
)
from app.schemas.wafer import (
    BinRecord,
    DieRecord,
    DieResult,
    WaferDataset,
    WaferMetadata,
    WaferSummary,
)
from app.validation.canonical import validate_dataset


def _issue(
    code: str,
    message: str,
    *,
    details: dict[str, object] | None = None,
) -> ValidationIssue:
    return ValidationIssue(
        severity=ValidationSeverity.ERROR,
        stage=ValidationStage.ASSEMBLE,
        code=code,
        message=message,
        details=details,
    )


def _normalize_notch(value: str | None) -> str | None:
    return value.upper() if value else None


def _compare_field(
    issues: list[ValidationIssue],
    *,
    field: str,
    pat_value: object,
    cp_value: object,
) -> None:
    if pat_value is None or cp_value is None:
        return
    if pat_value != cp_value:
        issues.append(
            _issue(
                "ASSEMBLY_METADATA_MISMATCH",
                f"PAT and CP disagree on {field}.",
                details={"field": field, "pat": pat_value, "cp": cp_value},
            )
        )


def _derive_bins(
    map_rows: list[str],
    definitions: list[SourceBinDefinition],
) -> tuple[list[BinRecord], list[ValidationIssue]]:
    issues: list[ValidationIssue] = []
    counts = Counter(char for row in map_rows for char in row if char != ".")
    definitions_by_char = {
        item.char: item for item in definitions if item.char is not None
    }

    for char, actual in counts.items():
        soft_bin = char_to_soft_bin(char)
        if soft_bin is None:
            issues.append(
                _issue(
                    "ASSEMBLY_UNKNOWN_BIN_CHAR",
                    f"Map character {char!r} has no Soft Bin mapping.",
                    details={"char": char},
                )
            )
            continue

        definition = definitions_by_char.get(char)
        if definitions and definition is None:
            issues.append(
                _issue(
                    "ASSEMBLY_BIN_DEFINITION_MISSING",
                    f"Soft Bin {soft_bin} is present in the map but absent from CP definitions.",
                    details={"soft_bin": soft_bin, "char": char, "actual": actual},
                )
            )

    canonical: list[BinRecord] = []
    if definitions:
        iterable = definitions
    else:
        iterable = [
            SourceBinDefinition(
                bin=soft_bin,
                char=char,
                declared_count=count,
            )
            for char, count in sorted(counts.items())
            if (soft_bin := char_to_soft_bin(char)) is not None
        ]

    tested = sum(counts.values())
    for item in iterable:
        char = item.char or soft_bin_to_char(item.bin)
        actual = counts.get(char, 0) if char is not None else 0
        if item.declared_count is not None and item.declared_count != actual:
            issues.append(
                _issue(
                    "ASSEMBLY_BIN_COUNT_MISMATCH",
                    f"Soft Bin {item.bin} declared count does not match map.",
                    details={
                        "soft_bin": item.bin,
                        "declared": item.declared_count,
                        "actual": actual,
                    },
                )
            )

        canonical.append(
            BinRecord(
                bin=item.bin,
                char=char,
                description=item.description,
                count=actual,
                percentage=(actual / tested) if tested else 0.0,
            )
        )

    return canonical, issues


class WaferAssembler:
    def assemble(self, parsed: list[SourceParseResult]) -> ParseResult:
        sources = [item.source for item in parsed]
        issues = [issue for item in parsed for issue in item.issues]

        if not parsed:
            issues.append(_issue("ASSEMBLY_NO_SOURCE", "No parsed source is available."))
            return ParseResult(
                dataset=None,
                sources=sources,
                validation_issues=issues,
                status=ParseStatus.INVALID,
            )

        pat_items = [
            item for item in parsed if item.source.detected_format == SourceFormat.PAT
        ]
        cp_items = [
            item for item in parsed if item.source.detected_format == SourceFormat.CP1
        ]

        if len(pat_items) > 1 or len(cp_items) > 1:
            issues.append(
                _issue(
                    "ASSEMBLY_DUPLICATE_SOURCE_ROLE",
                    "Only one PAT and one CP1 source may be assembled for one wafer.",
                    details={"pat_count": len(pat_items), "cp_count": len(cp_items)},
                )
            )

        if any(issue.severity == ValidationSeverity.ERROR for issue in issues):
            return ParseResult(
                dataset=None,
                sources=sources,
                validation_issues=issues,
                status=ParseStatus.INVALID,
            )

        pat = pat_items[0] if pat_items else None
        cp = cp_items[0] if cp_items else None
        primary = cp or pat
        if primary is None or primary.map_rows is None:
            issues.append(
                _issue(
                    "ASSEMBLY_MAP_MISSING",
                    "No source provides a complete wafer map.",
                )
            )
            return ParseResult(
                dataset=None,
                sources=sources,
                validation_issues=issues,
                status=ParseStatus.INVALID,
            )

        if pat is not None and cp is not None:
            _compare_field(
                issues,
                field="lot_id",
                pat_value=pat.metadata.lot_id,
                cp_value=cp.metadata.lot_id,
            )
            _compare_field(
                issues,
                field="wafer_id",
                pat_value=pat.metadata.wafer_id,
                cp_value=cp.metadata.wafer_id,
            )
            _compare_field(
                issues,
                field="rows",
                pat_value=pat.metadata.rows,
                cp_value=cp.metadata.rows,
            )
            _compare_field(
                issues,
                field="columns",
                pat_value=pat.metadata.columns,
                cp_value=cp.metadata.columns,
            )
            _compare_field(
                issues,
                field="notch",
                pat_value=_normalize_notch(pat.metadata.notch),
                cp_value=_normalize_notch(cp.metadata.notch),
            )
            if pat.map_rows != cp.map_rows:
                issues.append(
                    _issue(
                        "ASSEMBLY_MAP_MISMATCH",
                        "PAT and CP maps are not identical after outside-area normalization.",
                    )
                )

        if any(issue.severity == ValidationSeverity.ERROR for issue in issues):
            return ParseResult(
                dataset=None,
                sources=sources,
                validation_issues=issues,
                status=ParseStatus.INVALID,
            )

        map_rows = primary.map_rows
        source_metadata = primary.metadata
        definitions = cp.bins if cp is not None else primary.bins
        bins, bin_issues = _derive_bins(map_rows, definitions)
        issues.extend(bin_issues)

        description_by_bin = {item.bin: item.description for item in bins}
        pass_bins = {
            item.bin
            for item in bins
            if item.description and "PASS" in item.description.upper()
        }
        if not pass_bins:
            pass_bins = {1}

        dies: list[DieRecord] = []
        pass_die = 0
        fail_die = 0
        for row_index, row in enumerate(map_rows):
            for column_index, char in enumerate(row):
                if char == ".":
                    continue
                soft_bin = char_to_soft_bin(char)
                if soft_bin is None:
                    issues.append(
                        _issue(
                            "ASSEMBLY_UNKNOWN_BIN_CHAR",
                            f"Map character {char!r} has no Soft Bin mapping.",
                            details={
                                "char": char,
                                "row": row_index,
                                "column": column_index,
                            },
                        )
                    )
                    continue
                result = DieResult.PASS if soft_bin in pass_bins else DieResult.FAIL
                if result == DieResult.PASS:
                    pass_die += 1
                else:
                    fail_die += 1
                dies.append(
                    DieRecord(
                        row=row_index,
                        column=column_index,
                        source_char=char,
                        soft_bin=soft_bin,
                        result=result,
                        description=description_by_bin.get(soft_bin),
                    )
                )

        tested_die = len(dies)
        yield_value = (pass_die / tested_die) if tested_die else None

        metadata = WaferMetadata(
            product_id=(
                source_metadata.product_id
                or source_metadata.product_hint
                or (pat.metadata.product_hint if pat is not None else None)
            ),
            lot_id=source_metadata.lot_id,
            wafer_id=source_metadata.wafer_id,
            flow_id=source_metadata.flow_id,
            subcon=source_metadata.subcon,
            tester=source_metadata.tester,
            test_program=source_metadata.test_program,
            probe_card=source_metadata.probe_card,
            start_time=source_metadata.start_time,
            stop_time=source_metadata.stop_time,
            notch=_normalize_notch(source_metadata.notch),
            rows=len(map_rows),
            columns=len(map_rows[0]),
        )
        summary = WaferSummary(
            tested_die=tested_die,
            pass_die=pass_die,
            fail_die=fail_die,
            yield_=yield_value,
        )
        dataset = WaferDataset(
            metadata=metadata,
            dies=dies,
            bins=bins,
            summary=summary,
        )

        if cp is not None:
            declared = cp.metadata
            if declared.tested_die is not None and declared.tested_die != tested_die:
                issues.append(
                    _issue(
                        "ASSEMBLY_TESTED_MISMATCH",
                        "CP TESTED DIE does not match map.",
                        details={"declared": declared.tested_die, "actual": tested_die},
                    )
                )
            if declared.pass_die is not None and declared.pass_die != pass_die:
                issues.append(
                    _issue(
                        "ASSEMBLY_PASS_MISMATCH",
                        "CP PASS DIE does not match map.",
                        details={"declared": declared.pass_die, "actual": pass_die},
                    )
                )
            if (
                declared.yield_ is not None
                and yield_value is not None
                and abs(declared.yield_ - yield_value) > 0.00011
            ):
                issues.append(
                    _issue(
                        "ASSEMBLY_YIELD_MISMATCH",
                        "CP YIELD does not match map-derived yield.",
                        details={"declared": declared.yield_, "actual": yield_value},
                    )
                )

        issues.extend(validate_dataset(dataset))

        if any(issue.severity == ValidationSeverity.ERROR for issue in issues):
            return ParseResult(
                dataset=None,
                sources=sources,
                validation_issues=issues,
                status=ParseStatus.INVALID,
            )

        status = (
            ParseStatus.WARNING
            if any(issue.severity == ValidationSeverity.WARNING for issue in issues)
            else ParseStatus.VALID
        )
        return ParseResult(
            dataset=dataset,
            sources=sources,
            validation_issues=issues,
            status=status,
        )
