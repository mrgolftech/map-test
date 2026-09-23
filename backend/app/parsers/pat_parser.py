import re
from collections import Counter
from pathlib import Path

from app.parsers.base import (
    BaseParser,
    DetectionResult,
    RawSource,
    build_descriptor,
    decode_text,
)
from app.parsers.bin_codec import char_to_soft_bin
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

_NOTCH_RE = re.compile(r"^SOURCE\s+NOTCH\s*:\s*([A-Za-z]+)", re.IGNORECASE)


class PatParser(BaseParser):
    parser_id = "pat-v1"
    detected_format = SourceFormat.PAT
    role = SourceRole.COMBINED

    def detect(self, source: RawSource) -> DetectionResult:
        score = 0.0
        evidence: list[str] = []

        if Path(source.filename).suffix.lower() == ".pat":
            score += 0.25
            evidence.append("extension=.pat")

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

        lines = text.splitlines()
        if len(lines) >= 6 and _NOTCH_RE.match(lines[4].strip()):
            score += 0.35
            evidence.append("line5=SOURCE NOTCH")

        map_lines = [line for line in lines[5:] if line != ""]
        if len(map_lines) >= 4:
            widths = {len(line) for line in map_lines}
            allowed = sum(
                1
                for line in map_lines
                if all(char == "." or char_to_soft_bin(char) is not None for char in line)
            )
            if len(widths) == 1 and allowed / len(map_lines) >= 0.95:
                score += 0.50
                evidence.append("fixed-width single-character map")

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
                        message="PAT file is not valid UTF-8/ASCII text.",
                        source_file=source.filename,
                        details={"start": exc.start, "end": exc.end},
                    )
                ],
            )

        lines = text.splitlines()
        while lines and lines[-1] == "":
            lines.pop()

        if len(lines) < 6:
            return SourceParseResult(
                source=descriptor,
                metadata=SourceMetadata(),
                issues=[
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        stage=ValidationStage.PARSE,
                        code="PAT_TOO_SHORT",
                        message="PAT file does not contain the expected header and map.",
                        source_file=source.filename,
                    )
                ],
            )

        product_hint = lines[0].strip() or None
        lot_id = lines[1].strip() or None
        wafer_token = lines[2].strip()
        wafer_id = wafer_token.rsplit("-", 1)[-1] if "-" in wafer_token else wafer_token or None

        notch_match = _NOTCH_RE.match(lines[4].strip())
        notch = notch_match.group(1).upper() if notch_match else None
        if notch is None:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    stage=ValidationStage.PARSE,
                    code="PAT_NOTCH_MISSING",
                    message="PAT SOURCE NOTCH header is missing or invalid.",
                    source_file=source.filename,
                    line=5,
                )
            )

        map_rows = lines[5:]
        columns = max((len(row) for row in map_rows), default=0)
        if columns == 0:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    stage=ValidationStage.PARSE,
                    code="PAT_EMPTY_MAP",
                    message="PAT map contains no columns.",
                    source_file=source.filename,
                )
            )

        for index, row in enumerate(map_rows, start=1):
            if len(row) != columns:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        stage=ValidationStage.PARSE,
                        code="PARSER_ROW_LENGTH_MISMATCH",
                        message="PAT map row length does not match inferred columns.",
                        source_file=source.filename,
                        line=index + 5,
                        row=index - 1,
                        details={"expected": columns, "actual": len(row)},
                    )
                )
                continue

            for column, char in enumerate(row):
                if char == ".":
                    continue
                if char_to_soft_bin(char) is None:
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            stage=ValidationStage.PARSE,
                            code="PARSER_UNKNOWN_BIN_CHAR",
                            message=f"Unknown PAT bin character {char!r}.",
                            source_file=source.filename,
                            line=index + 5,
                            row=index - 1,
                            column=column,
                            details={"char": char},
                        )
                    )

        counts = Counter(char for row in map_rows for char in row if char != ".")
        bins = [
            SourceBinDefinition(
                bin=soft_bin,
                char=char,
                declared_count=count,
            )
            for char, count in sorted(counts.items(), key=lambda item: item[0])
            if (soft_bin := char_to_soft_bin(char)) is not None
        ]

        return SourceParseResult(
            source=descriptor,
            metadata=SourceMetadata(
                product_hint=product_hint,
                lot_id=lot_id,
                wafer_id=wafer_id,
                notch=notch,
                rows=len(map_rows) or None,
                columns=columns or None,
            ),
            map_rows=map_rows or None,
            bins=bins,
            issues=issues,
        )
