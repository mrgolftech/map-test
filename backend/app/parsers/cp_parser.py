import re
from datetime import datetime
from pathlib import Path

from app.parsers.base import (
    BaseParser,
    DetectionResult,
    RawSource,
    build_descriptor,
    decode_text,
)
from app.parsers.bin_codec import char_to_soft_bin, soft_bin_to_char
from app.schemas.parsing import (
    SourceBinDefinition,
    SourceFormat,
    SourceMetadata,
    SourceParseResult,
    SourceRole,
    ValidationIssue,
    ValidationSeverity,
    ValidationStage,
)

_BIN_RE = re.compile(
    r"^\s*BIN,\s*(\d+),\s*(\d+),\s*([0-9.]+)%,\s*\{\[(.*?)\]\}\s*$"
)
_MAP_ROW_RE = re.compile(r"^(\d{3})  (.*)$")


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.strptime(value, "%Y/%m/%d %H:%M:%S")


class CpParser(BaseParser):
    parser_id = "cp1-v1"
    detected_format = SourceFormat.CP1
    role = SourceRole.COMBINED

    def detect(self, source: RawSource) -> DetectionResult:
        score = 0.0
        evidence: list[str] = []
        suffix = Path(source.filename).suffix.lower()

        if suffix == ".cp1":
            score += 0.25
            evidence.append("extension=.cp1")

        try:
            text = decode_text(source)
        except UnicodeDecodeError:
            return DetectionResult(
                parser_id=self.parser_id,
                detected_format=self.detected_format,
                role=self.role,
                score=score,
                evidence=tuple(evidence),
            )

        required_sections = ("[BOF]", "[SOFT BIN]", "[SOFT BIN MAP]", "[EOF]")
        present = [section for section in required_sections if section in text]
        if len(present) == len(required_sections):
            score += 0.55
            evidence.append("BOF/SOFT BIN/SOFT BIN MAP/EOF sections")
        elif present:
            score += 0.10
            evidence.append("partial CP sections")

        if "MAP ROW" in text and "MAP COLUMN" in text and "TESTED DIE" in text:
            score += 0.20
            evidence.append("CP metadata keys")

        return DetectionResult(
            parser_id=self.parser_id,
            detected_format=self.detected_format,
            role=self.role,
            score=min(score, 1.0),
            evidence=tuple(evidence),
        )

    def parse(self, source: RawSource, detection: DetectionResult) -> SourceParseResult:
        descriptor = build_descriptor(source, detection)
        issues: list[ValidationIssue] = []

        try:
            text = decode_text(source)
        except UnicodeDecodeError as exc:
            return SourceParseResult(
                source=descriptor,
                metadata=SourceMetadata(),
                issues=[
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        stage=ValidationStage.PARSE,
                        code="PARSER_ENCODING_ERROR",
                        message="CP file is not valid UTF-8/ASCII text.",
                        source_file=source.filename,
                        details={"start": exc.start, "end": exc.end},
                    )
                ],
            )

        section_positions = {
            name: text.find(name)
            for name in ("[BOF]", "[SOFT BIN]", "[SOFT BIN MAP]", "[EXTENSION]", "[EOF]")
        }
        for required in ("[BOF]", "[SOFT BIN]", "[SOFT BIN MAP]", "[EOF]"):
            if section_positions[required] < 0:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        stage=ValidationStage.PARSE,
                        code="CP_SECTION_MISSING",
                        message=f"Required CP section {required} is missing.",
                        source_file=source.filename,
                        details={"section": required},
                    )
                )

        if any(issue.severity == ValidationSeverity.ERROR for issue in issues):
            return SourceParseResult(
                source=descriptor,
                metadata=SourceMetadata(),
                issues=issues,
            )

        header_text = text[
            section_positions["[BOF]"] + len("[BOF]") : section_positions["[SOFT BIN]"]
        ]
        raw_header: dict[str, str] = {}
        for line in header_text.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            raw_header[key.strip().upper()] = value.strip()

        def int_header(key: str) -> int | None:
            value = raw_header.get(key)
            if value in (None, ""):
                return None
            try:
                return int(value)
            except ValueError:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        stage=ValidationStage.PARSE,
                        code="CP_HEADER_INTEGER_INVALID",
                        message=f"CP header {key} is not an integer.",
                        source_file=source.filename,
                        details={"key": key, "value": value},
                    )
                )
                return None

        def percent_header(key: str) -> float | None:
            value = raw_header.get(key)
            if value in (None, ""):
                return None
            try:
                return float(value.rstrip("%")) / 100.0
            except ValueError:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        stage=ValidationStage.PARSE,
                        code="CP_HEADER_PERCENT_INVALID",
                        message=f"CP header {key} is not a percentage.",
                        source_file=source.filename,
                        details={"key": key, "value": value},
                    )
                )
                return None

        rows = int_header("MAP ROW")
        columns = int_header("MAP COLUMN")
        tested_die = int_header("TESTED DIE")
        pass_die = int_header("PASS DIE")

        start_time = None
        stop_time = None
        try:
            start_time = _parse_datetime(raw_header.get("START TIME"))
            stop_time = _parse_datetime(raw_header.get("STOP TIME"))
        except ValueError as exc:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    stage=ValidationStage.PARSE,
                    code="CP_DATETIME_INVALID",
                    message="CP START TIME or STOP TIME has an invalid format.",
                    source_file=source.filename,
                    details={"error": str(exc)},
                )
            )

        bin_text = text[
            section_positions["[SOFT BIN]"] + len("[SOFT BIN]") :
            section_positions["[SOFT BIN MAP]"]
        ]
        bins: list[SourceBinDefinition] = []
        for line_number, line in enumerate(bin_text.splitlines(), start=1):
            match = _BIN_RE.match(line)
            if not match:
                continue
            soft_bin = int(match.group(1))
            count = int(match.group(2))
            percentage = float(match.group(3)) / 100.0
            description = match.group(4).strip() or None
            char = soft_bin_to_char(soft_bin)
            if count > 0 and char is None:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        stage=ValidationStage.PARSE,
                        code="CP_BIN_CHAR_UNSUPPORTED",
                        message=f"Soft Bin {soft_bin} cannot be represented by MAP BIN LENGTH 1.",
                        source_file=source.filename,
                        details={"soft_bin": soft_bin, "count": count},
                    )
                )
            bins.append(
                SourceBinDefinition(
                    bin=soft_bin,
                    char=char,
                    description=description,
                    declared_count=count,
                    declared_percentage=percentage,
                )
            )

        map_start = section_positions["[SOFT BIN MAP]"] + len("[SOFT BIN MAP]")
        map_end_candidates = [
            position
            for key, position in section_positions.items()
            if key in ("[EXTENSION]", "[EOF]") and position > map_start
        ]
        map_end = min(map_end_candidates) if map_end_candidates else len(text)
        map_text = text[map_start:map_end]

        map_rows_by_number: dict[int, str] = {}
        for line in map_text.splitlines():
            match = _MAP_ROW_RE.match(line)
            if not match:
                continue
            row_number = int(match.group(1))
            raw_row = match.group(2)

            if rows is not None and row_number > rows:
                if not raw_row.strip():
                    continue
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        stage=ValidationStage.PARSE,
                        code="CP_EXTRA_MAP_ROW",
                        message="CP contains a non-empty map row beyond MAP ROW.",
                        source_file=source.filename,
                        row=row_number - 1,
                        details={"declared_rows": rows},
                    )
                )
                continue

            if columns is not None and len(raw_row) != columns:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        stage=ValidationStage.PARSE,
                        code="PARSER_ROW_LENGTH_MISMATCH",
                        message="CP map row length does not match MAP COLUMN.",
                        source_file=source.filename,
                        row=row_number - 1,
                        details={"expected": columns, "actual": len(raw_row)},
                    )
                )
                continue

            normalized = raw_row.replace(" ", ".")
            map_rows_by_number[row_number] = normalized

            for column, char in enumerate(normalized):
                if char == ".":
                    continue
                soft_bin = char_to_soft_bin(char)
                if soft_bin is None:
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            stage=ValidationStage.PARSE,
                            code="PARSER_UNKNOWN_BIN_CHAR",
                            message=f"Unknown CP bin character {char!r}.",
                            source_file=source.filename,
                            row=row_number - 1,
                            column=column,
                            details={"char": char},
                        )
                    )

        map_rows: list[str] | None = None
        if rows is not None:
            missing = [row for row in range(1, rows + 1) if row not in map_rows_by_number]
            if missing:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        stage=ValidationStage.PARSE,
                        code="CP_MAP_ROW_MISSING",
                        message="CP map is missing one or more declared rows.",
                        source_file=source.filename,
                        details={"missing_rows": missing[:20], "missing_count": len(missing)},
                    )
                )
            else:
                map_rows = [map_rows_by_number[row] for row in range(1, rows + 1)]

        return SourceParseResult(
            source=descriptor,
            metadata=SourceMetadata(
                product_id=raw_header.get("PRODUCT ID") or None,
                lot_id=raw_header.get("LOT ID") or None,
                wafer_id=raw_header.get("WAFER ID") or None,
                flow_id=raw_header.get("FLOW ID") or None,
                subcon=raw_header.get("SUBCON") or None,
                tester=raw_header.get("TESTER NAME") or None,
                test_program=raw_header.get("TEST PROGRAM") or None,
                probe_card=raw_header.get("PROBE CARD ID") or None,
                start_time=start_time,
                stop_time=stop_time,
                notch=(raw_header.get("SOURCE NOTCH") or "").upper() or None,
                rows=rows,
                columns=columns,
                tested_die=tested_die,
                pass_die=pass_die,
                yield_=percent_header("YIELD"),
            ),
            map_rows=map_rows,
            bins=bins,
            issues=issues,
        )
