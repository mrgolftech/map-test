from collections import Counter, defaultdict
from datetime import UTC, datetime
from math import sqrt
from statistics import mean, median, pstdev

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db.models import AnalysisRecord
from app.repositories.analysis_repository import AnalysisRepository
from app.schemas.analysis import AnalysisSummary, SpatialBinStat
from app.schemas.comparison import (
    BinAggregate,
    BinTrendPoint,
    ComparisonData,
    CompatibilityIssue,
    CompatibilityResult,
    CompatibilitySeverity,
    LotListItem,
    PatternDistributionItem,
    PreviewBin,
    WaferComparisonRow,
    WaferMapPreview,
    YieldAggregate,
    YieldTrendPoint,
)
from app.schemas.wafer import WaferDataset


class _LoadedAnalysis:
    def __init__(self, record: AnalysisRecord) -> None:
        self.record = record
        self.dataset = WaferDataset.model_validate_json(record.dataset_json)
        self.analysis = AnalysisSummary.model_validate_json(
            record.analysis_summary_json
        )

    @property
    def test_time(self) -> datetime:
        value = (
            self.dataset.metadata.stop_time
            or self.dataset.metadata.start_time
            or self.record.created_at
        )
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


def _quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * q
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(ordered) - 1)
    fraction = position - lower_index
    return ordered[lower_index] + (
        ordered[upper_index] - ordered[lower_index]
    ) * fraction


def _average_optional(values: list[float | None]) -> float | None:
    present = [value for value in values if value is not None]
    return mean(present) if present else None


def _std(values: list[float]) -> float:
    return pstdev(values) if len(values) > 1 else 0.0


def _bin_signature(dataset: WaferDataset) -> tuple[tuple[int, str | None, str], ...]:
    return tuple(
        sorted(
            (
                item.bin,
                item.char,
                item.description or "",
            )
            for item in dataset.bins
        )
    )


def _preview(dataset: WaferDataset) -> WaferMapPreview:
    rows = [
        ["."] * dataset.metadata.columns
        for _ in range(dataset.metadata.rows)
    ]
    for die in dataset.dies:
        rows[die.row][die.column] = die.source_char

    return WaferMapPreview(
        rows=dataset.metadata.rows,
        columns=dataset.metadata.columns,
        notch=dataset.metadata.notch,
        map_rows=["".join(row) for row in rows],
        bins=[
            PreviewBin(
                soft_bin=item.bin,
                char=item.char,
                description=item.description,
            )
            for item in dataset.bins
        ],
    )


def _spatial_for(
    analysis: AnalysisSummary,
    soft_bin: int | None,
) -> SpatialBinStat | None:
    if soft_bin is None:
        return None
    return next(
        (
            item
            for item in analysis.spatial_by_bin
            if item.soft_bin == soft_bin
        ),
        None,
    )


def _bin_stat_for(analysis: AnalysisSummary, soft_bin: int | None):
    if soft_bin is None:
        return None
    return next(
        (
            item
            for item in analysis.bin_stats
            if item.soft_bin == soft_bin
        ),
        None,
    )


class LotComparisonService:
    preview_limit = 12

    def __init__(self, session: Session) -> None:
        self._repository = AnalysisRepository(session)

    def list_lots(self) -> list[LotListItem]:
        return [
            LotListItem.model_validate(item)
            for item in self._repository.list_lots()
        ]

    def compare_ids(self, analysis_ids: list[str]) -> ComparisonData:
        if len(set(analysis_ids)) != len(analysis_ids):
            raise AppError(
                code="COMPARE_DUPLICATE_ANALYSIS_ID",
                message="Comparison analysis IDs must be unique.",
                status_code=422,
            )

        records = self._repository.get_many(analysis_ids)
        found = {record.id for record in records}
        missing = [
            analysis_id
            for analysis_id in analysis_ids
            if analysis_id not in found
        ]
        if missing:
            raise AppError(
                code="ANALYSIS_NOT_FOUND",
                message="One or more analysis records were not found.",
                status_code=404,
                details={"missing_analysis_ids": missing},
            )
        return self._compare(records)

    def summarize_lot(
        self,
        *,
        lot_id: str,
        product_id: str | None,
    ) -> ComparisonData:
        records = self._repository.list_by_lot(
            lot_id=lot_id,
            product_id=product_id,
        )
        if not records:
            raise AppError(
                code="LOT_NOT_FOUND",
                message="Lot has no persisted analysis records.",
                status_code=404,
                details={
                    "lot_id": lot_id,
                    "product_id": product_id,
                },
            )

        if product_id is None:
            products = {record.product_id for record in records}
            if len(products) > 1:
                raise AppError(
                    code="LOT_AMBIGUOUS",
                    message=(
                        "The same lot ID exists under multiple products; "
                        "product_id is required."
                    ),
                    status_code=409,
                    details={
                        "lot_id": lot_id,
                        "product_ids": sorted(
                            value for value in products if value is not None
                        ),
                        "contains_null_product": None in products,
                    },
                )

        return self._compare(records)

    def _compare(self, records: list[AnalysisRecord]) -> ComparisonData:
        if len(records) < 2:
            raise AppError(
                code="COMPARE_TOO_FEW_WAFERS",
                message="At least two wafer analyses are required.",
                status_code=422,
            )

        loaded = [_LoadedAnalysis(record) for record in records]
        loaded.sort(key=lambda item: (item.test_time, item.record.id))

        compatibility = self._compatibility(loaded)
        limitations = [
            issue.message
            for issue in compatibility.issues
            if issue.severity != CompatibilitySeverity.INFO
        ]
        if not compatibility.compatible:
            limitations.append(
                "Aggregate statistics are descriptive only because compatibility errors exist."
            )

        yield_values = [
            item.dataset.summary.yield_
            for item in loaded
            if item.dataset.summary.yield_ is not None
        ]
        yield_stats, lower, upper = self._yield_stats(
            [float(value) for value in yield_values]
        )
        if len(yield_values) < 4:
            limitations.append(
                "IQR outlier detection requires at least 4 wafers; no yield outliers were flagged."
            )

        outlier_by_id: dict[str, tuple[bool, str | None]] = {}
        for item in loaded:
            value = item.dataset.summary.yield_
            outlier = (
                value is not None
                and lower is not None
                and upper is not None
                and (value < lower or value > upper)
            )
            reason = None
            if outlier and value is not None:
                reason = (
                    f"yield={value:.6f} outside IQR bounds "
                    f"[{lower:.6f}, {upper:.6f}]"
                )
            outlier_by_id[item.record.id] = (outlier, reason)

        yield_trend = [
            YieldTrendPoint(
                analysis_id=item.record.id,
                wafer_id=item.dataset.metadata.wafer_id,
                test_time=item.test_time,
                yield_=item.dataset.summary.yield_,
                is_outlier=outlier_by_id[item.record.id][0],
                outlier_reason=outlier_by_id[item.record.id][1],
            )
            for item in loaded
        ]

        rows = [
            self._row(
                item,
                outlier=outlier_by_id[item.record.id][0],
                include_preview=index < self.preview_limit,
            )
            for index, item in enumerate(loaded)
        ]
        if len(loaded) > self.preview_limit:
            limitations.append(
                f"Mini-map previews are limited to the first {self.preview_limit} wafers."
            )

        product_ids = {
            item.dataset.metadata.product_id
            for item in loaded
        }
        lot_ids = {
            item.dataset.metadata.lot_id
            for item in loaded
        }

        return ComparisonData(
            product_id=next(iter(product_ids)) if len(product_ids) == 1 else None,
            lot_id=next(iter(lot_ids)) if len(lot_ids) == 1 else None,
            compatibility=compatibility,
            yield_stats=yield_stats,
            yield_trend=yield_trend,
            bin_aggregates=self._bin_aggregates(loaded),
            pattern_distribution=self._pattern_distribution(loaded),
            wafers=rows,
            limitations=list(dict.fromkeys(limitations)),
        )

    def _compatibility(
        self,
        loaded: list[_LoadedAnalysis],
    ) -> CompatibilityResult:
        issues: list[CompatibilityIssue] = []

        self._check_equal(
            issues,
            code="PRODUCT_MISMATCH",
            label="Product",
            values=[item.dataset.metadata.product_id for item in loaded],
            severity=CompatibilitySeverity.ERROR,
        )
        self._check_equal(
            issues,
            code="FLOW_MISMATCH",
            label="Flow",
            values=[item.dataset.metadata.flow_id for item in loaded],
            severity=CompatibilitySeverity.ERROR,
        )
        self._check_equal(
            issues,
            code="GEOMETRY_MISMATCH",
            label="Map geometry",
            values=[
                (
                    item.dataset.metadata.rows,
                    item.dataset.metadata.columns,
                )
                for item in loaded
            ],
            severity=CompatibilitySeverity.ERROR,
        )
        self._check_equal(
            issues,
            code="BIN_DEFINITION_MISMATCH",
            label="Soft Bin definitions",
            values=[_bin_signature(item.dataset) for item in loaded],
            severity=CompatibilitySeverity.ERROR,
        )
        self._check_equal(
            issues,
            code="LOT_DIFFERENT",
            label="Lot",
            values=[item.dataset.metadata.lot_id for item in loaded],
            severity=CompatibilitySeverity.INFO,
        )
        self._check_equal(
            issues,
            code="TESTER_DIFFERENT",
            label="Tester",
            values=[item.dataset.metadata.tester for item in loaded],
            severity=CompatibilitySeverity.WARNING,
        )
        self._check_equal(
            issues,
            code="TEST_PROGRAM_DIFFERENT",
            label="Test Program",
            values=[item.dataset.metadata.test_program for item in loaded],
            severity=CompatibilitySeverity.WARNING,
        )
        self._check_equal(
            issues,
            code="PROBE_CARD_DIFFERENT",
            label="Probe Card",
            values=[item.dataset.metadata.probe_card for item in loaded],
            severity=CompatibilitySeverity.WARNING,
        )

        compatible = not any(
            issue.severity == CompatibilitySeverity.ERROR
            for issue in issues
        )
        return CompatibilityResult(
            compatible=compatible,
            issues=issues,
        )

    @staticmethod
    def _check_equal(
        issues: list[CompatibilityIssue],
        *,
        code: str,
        label: str,
        values: list[object],
        severity: CompatibilitySeverity,
    ) -> None:
        normalized = {repr(value) for value in values}
        if len(normalized) <= 1:
            return
        issues.append(
            CompatibilityIssue(
                severity=severity,
                code=code,
                message=f"{label} differs across selected wafers.",
                details={
                    "values": sorted(normalized),
                },
            )
        )

    @staticmethod
    def _yield_stats(
        values: list[float],
    ) -> tuple[YieldAggregate, float | None, float | None]:
        q1 = _quantile(values, 0.25)
        q3 = _quantile(values, 0.75)
        iqr = (q3 - q1) if q1 is not None and q3 is not None else None
        lower = None
        upper = None
        if len(values) >= 4 and iqr is not None and q1 is not None and q3 is not None:
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr

        stats = YieldAggregate(
            wafer_count=len(values),
            valid_yield_count=len(values),
            average=mean(values) if values else None,
            median=median(values) if values else None,
            std_dev=pstdev(values) if len(values) > 1 else (0.0 if values else None),
            minimum=min(values) if values else None,
            maximum=max(values) if values else None,
            q1=q1,
            q3=q3,
            iqr=iqr,
            outlier_lower_bound=lower,
            outlier_upper_bound=upper,
        )
        return stats, lower, upper

    def _row(
        self,
        loaded: _LoadedAnalysis,
        *,
        outlier: bool,
        include_preview: bool,
    ) -> WaferComparisonRow:
        record = loaded.record
        dataset = loaded.dataset
        analysis = loaded.analysis
        main_bin = record.main_fail_bin
        bin_stat = _bin_stat_for(analysis, main_bin)
        spatial = _spatial_for(analysis, main_bin)

        return WaferComparisonRow(
            analysis_id=record.id,
            product_id=dataset.metadata.product_id,
            lot_id=dataset.metadata.lot_id,
            wafer_id=dataset.metadata.wafer_id,
            flow_id=dataset.metadata.flow_id,
            test_time=loaded.test_time,
            yield_=dataset.summary.yield_,
            tested_die=dataset.summary.tested_die,
            pass_die=dataset.summary.pass_die,
            fail_die=dataset.summary.fail_die,
            main_fail_bin=main_bin,
            main_fail_rate=bin_stat.wafer_rate if bin_stat else None,
            edge_enrichment=spatial.edge.enrichment if spatial else None,
            center_enrichment=spatial.center.enrichment if spatial else None,
            cluster_ratio=spatial.cluster.cluster_ratio if spatial else None,
            main_pattern=record.main_pattern,
            tester=dataset.metadata.tester,
            test_program=dataset.metadata.test_program,
            probe_card=dataset.metadata.probe_card,
            is_outlier=outlier,
            preview=_preview(dataset) if include_preview else None,
        )

    def _bin_aggregates(
        self,
        loaded: list[_LoadedAnalysis],
    ) -> list[BinAggregate]:
        by_bin: dict[int, list[tuple[_LoadedAnalysis, object]]] = defaultdict(list)
        for item in loaded:
            for bin_stat in item.analysis.bin_stats:
                by_bin[bin_stat.soft_bin].append((item, bin_stat))

        result: list[BinAggregate] = []
        for soft_bin, entries in sorted(by_bin.items()):
            rates = [float(stat.wafer_rate) for _, stat in entries]
            fail_shares = [stat.fail_share for _, stat in entries]
            edge_values: list[float | None] = []
            center_values: list[float | None] = []
            trend: list[BinTrendPoint] = []

            for item, stat in entries:
                spatial = _spatial_for(item.analysis, soft_bin)
                edge = spatial.edge.enrichment if spatial else None
                center = spatial.center.enrichment if spatial else None
                edge_values.append(edge)
                center_values.append(center)
                trend.append(
                    BinTrendPoint(
                        analysis_id=item.record.id,
                        wafer_id=item.dataset.metadata.wafer_id,
                        test_time=item.test_time,
                        wafer_rate=stat.wafer_rate,
                        fail_share=stat.fail_share,
                        edge_enrichment=edge,
                        center_enrichment=center,
                    )
                )

            first_stat = entries[0][1]
            result.append(
                BinAggregate(
                    soft_bin=soft_bin,
                    char=first_stat.char,
                    description=first_stat.description,
                    wafer_count=len(entries),
                    mean_wafer_rate=mean(rates),
                    std_wafer_rate=_std(rates),
                    mean_fail_share=_average_optional(fail_shares),
                    mean_edge_enrichment=_average_optional(edge_values),
                    mean_center_enrichment=_average_optional(center_values),
                    trend=trend,
                )
            )

        return result

    @staticmethod
    def _pattern_distribution(
        loaded: list[_LoadedAnalysis],
    ) -> list[PatternDistributionItem]:
        counts = Counter(
            item.record.main_pattern or "NONE"
            for item in loaded
        )
        total = len(loaded)
        return [
            PatternDistributionItem(
                pattern=pattern,
                count=count,
                percentage=count / total,
            )
            for pattern, count in counts.most_common()
        ]
