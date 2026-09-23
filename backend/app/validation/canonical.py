from collections import Counter

from app.schemas.parsing import (
    ValidationIssue,
    ValidationSeverity,
    ValidationStage,
)
from app.schemas.wafer import WaferDataset


def validate_dataset(dataset: WaferDataset) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    metadata = dataset.metadata
    summary = dataset.summary

    coordinates = [(die.row, die.column) for die in dataset.dies]
    if len(coordinates) != len(set(coordinates)):
        issues.append(
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                stage=ValidationStage.CANONICAL,
                code="CANONICAL_DUPLICATE_COORDINATE",
                message="WaferDataset contains duplicate die coordinates.",
            )
        )

    out_of_range = [
        (die.row, die.column)
        for die in dataset.dies
        if die.row >= metadata.rows or die.column >= metadata.columns
    ]
    if out_of_range:
        issues.append(
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                stage=ValidationStage.CANONICAL,
                code="CANONICAL_COORDINATE_OUT_OF_RANGE",
                message="WaferDataset contains die coordinates outside declared geometry.",
                details={"coordinates": out_of_range[:20], "count": len(out_of_range)},
            )
        )

    if summary.tested_die != len(dataset.dies):
        issues.append(
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                stage=ValidationStage.CANONICAL,
                code="CANONICAL_TESTED_MISMATCH",
                message="Tested die count does not match canonical die records.",
                details={"summary": summary.tested_die, "dies": len(dataset.dies)},
            )
        )

    if summary.tested_die != summary.pass_die + summary.fail_die:
        issues.append(
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                stage=ValidationStage.CANONICAL,
                code="CANONICAL_PASS_FAIL_MISMATCH",
                message="Tested die must equal pass die plus fail die.",
                details={
                    "tested": summary.tested_die,
                    "pass": summary.pass_die,
                    "fail": summary.fail_die,
                },
            )
        )

    actual_by_bin = Counter(
        die.soft_bin for die in dataset.dies if die.soft_bin is not None
    )
    declared_by_bin = {item.bin: item.count for item in dataset.bins}
    for soft_bin, actual in actual_by_bin.items():
        declared = declared_by_bin.get(soft_bin)
        if declared != actual:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    stage=ValidationStage.CANONICAL,
                    code="CANONICAL_BIN_COUNT_MISMATCH",
                    message=f"Soft Bin {soft_bin} count does not match die records.",
                    details={
                        "soft_bin": soft_bin,
                        "declared": declared,
                        "actual": actual,
                    },
                )
            )

    if sum(item.count for item in dataset.bins) != summary.tested_die:
        issues.append(
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                stage=ValidationStage.CANONICAL,
                code="CANONICAL_BIN_TOTAL_MISMATCH",
                message="Sum of canonical Bin counts does not equal tested die.",
                details={
                    "bin_total": sum(item.count for item in dataset.bins),
                    "tested": summary.tested_die,
                },
            )
        )

    return issues
