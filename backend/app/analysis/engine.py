from collections import Counter, defaultdict

from app.analysis.clustering import connected_components
from app.analysis.geometry import DieGeometry, build_geometry
from app.schemas.analysis import (
    AnalysisConfig,
    AnalysisSummary,
    BinRegionMetric,
    BinStat,
    PatternResult,
    RegionMetric,
    SpatialBinStat,
)
from app.schemas.wafer import DieRecord, DieResult, WaferDataset


_REGION_NAMES = (
    "center",
    "mid",
    "edge",
    "top",
    "bottom",
    "left",
    "right",
    "q1",
    "q2",
    "q3",
    "q4",
)


def _safe_rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _region_membership(geometry: DieGeometry) -> tuple[str, ...]:
    return (
        geometry.radial_region,
        geometry.vertical_region,
        geometry.horizontal_region,
        geometry.quadrant,
    )


def _region_metric(dies: list[DieRecord]) -> RegionMetric:
    tested = len(dies)
    passed = sum(1 for die in dies if die.result == DieResult.PASS)
    failed = sum(1 for die in dies if die.result == DieResult.FAIL)
    return RegionMetric(
        tested_die=tested,
        pass_die=passed,
        fail_die=failed,
        fail_rate=_safe_rate(failed, tested),
    )


def _bin_region_metric(
    *,
    region_tested: int,
    region_bin_count: int,
    whole_tested: int,
    whole_bin_count: int,
) -> BinRegionMetric:
    region_rate = _safe_rate(region_bin_count, region_tested)
    whole_rate = _safe_rate(whole_bin_count, whole_tested)
    enrichment = (
        region_rate / whole_rate
        if region_rate is not None and whole_rate not in (None, 0.0)
        else None
    )
    return BinRegionMetric(
        tested_die=region_tested,
        bin_die=region_bin_count,
        region_rate=region_rate,
        whole_rate=whole_rate,
        enrichment=enrichment,
    )


def _score_enrichment(value: float | None, threshold: float) -> float:
    if value is None or value < threshold:
        return 0.0
    progress = min((value - threshold) / threshold, 1.0)
    return min(1.0, 0.60 + 0.40 * progress)


def _pattern(
    name: str,
    soft_bin: int,
    score: float,
    evidence: list[str],
    thresholds: dict[str, float | int | str],
    limitations: list[str] | None = None,
) -> PatternResult:
    return PatternResult(
        pattern=name,
        soft_bin=soft_bin,
        score=score,
        evidence=evidence,
        thresholds=thresholds,
        limitations=limitations or [],
    )


def _detect_patterns(
    stat: SpatialBinStat,
    config: AnalysisConfig,
) -> list[PatternResult]:
    if stat.count <= 0:
        return []

    results: list[PatternResult] = []
    enrichment_threshold = config.enrichment_threshold

    edge_score = _score_enrichment(stat.edge.enrichment, enrichment_threshold)
    if edge_score:
        results.append(
            _pattern(
                "EDGE",
                stat.soft_bin,
                edge_score,
                [
                    f"edge_enrichment={stat.edge.enrichment:.3f}",
                    f"edge_bin_rate={stat.edge.region_rate:.4f}",
                    f"whole_bin_rate={stat.edge.whole_rate:.4f}",
                ],
                {"enrichment_threshold": enrichment_threshold},
            )
        )

    center_score = _score_enrichment(stat.center.enrichment, enrichment_threshold)
    if center_score:
        results.append(
            _pattern(
                "CENTER",
                stat.soft_bin,
                center_score,
                [
                    f"center_enrichment={stat.center.enrichment:.3f}",
                    f"center_bin_rate={stat.center.region_rate:.4f}",
                    f"whole_bin_rate={stat.center.whole_rate:.4f}",
                ],
                {"enrichment_threshold": enrichment_threshold},
            )
        )

    mid_enrichment = stat.mid.enrichment
    edge_enrichment = stat.edge.enrichment or 0.0
    center_enrichment = stat.center.enrichment or 0.0
    if (
        mid_enrichment is not None
        and mid_enrichment >= enrichment_threshold
        and edge_enrichment < 1.20
        and center_enrichment < 1.20
    ):
        results.append(
            _pattern(
                "RING",
                stat.soft_bin,
                _score_enrichment(mid_enrichment, enrichment_threshold),
                [
                    f"mid_enrichment={mid_enrichment:.3f}",
                    f"edge_enrichment={edge_enrichment:.3f}",
                    f"center_enrichment={center_enrichment:.3f}",
                ],
                {
                    "mid_enrichment_threshold": enrichment_threshold,
                    "outer_region_max_enrichment": 1.20,
                },
            )
        )

    directional_pairs = (
        ("TOP", stat.top, stat.bottom),
        ("BOTTOM", stat.bottom, stat.top),
        ("LEFT", stat.left, stat.right),
        ("RIGHT", stat.right, stat.left),
    )
    for name, target, opposite in directional_pairs:
        target_score = _score_enrichment(
            target.enrichment,
            config.directional_enrichment_threshold,
        )
        if target_score and (opposite.enrichment or 0.0) <= 1.10:
            results.append(
                _pattern(
                    name,
                    stat.soft_bin,
                    target_score,
                    [
                        f"{name.lower()}_enrichment={target.enrichment:.3f}",
                        f"opposite_enrichment={(opposite.enrichment or 0.0):.3f}",
                    ],
                    {
                        "directional_enrichment_threshold":
                            config.directional_enrichment_threshold,
                        "opposite_max_enrichment": 1.10,
                    },
                )
            )

    for name, metric in (
        ("Q1", stat.q1),
        ("Q2", stat.q2),
        ("Q3", stat.q3),
        ("Q4", stat.q4),
    ):
        quadrant_score = _score_enrichment(
            metric.enrichment,
            config.directional_enrichment_threshold,
        )
        if quadrant_score and metric.bin_die >= config.min_cluster_size:
            results.append(
                _pattern(
                    "QUADRANT",
                    stat.soft_bin,
                    quadrant_score,
                    [
                        f"quadrant={name}",
                        f"quadrant_enrichment={metric.enrichment:.3f}",
                        f"quadrant_bin_die={metric.bin_die}",
                    ],
                    {
                        "directional_enrichment_threshold":
                            config.directional_enrichment_threshold,
                        "minimum_bin_die": config.min_cluster_size,
                    },
                )
            )

    cluster_ratio = stat.cluster.cluster_ratio or 0.0
    if (
        stat.cluster.largest_component >= config.min_cluster_size
        and cluster_ratio >= config.cluster_ratio_threshold
    ):
        results.append(
            _pattern(
                "LOCALIZED_CLUSTER",
                stat.soft_bin,
                min(1.0, 0.60 + 0.40 * cluster_ratio),
                [
                    f"largest_component={stat.cluster.largest_component}",
                    f"cluster_ratio={cluster_ratio:.3f}",
                    f"component_count={stat.cluster.component_count}",
                ],
                {
                    "min_cluster_size": config.min_cluster_size,
                    "cluster_ratio_threshold": config.cluster_ratio_threshold,
                    "neighbor_mode": config.neighbor_mode,
                },
            )
        )

    row_fraction = stat.max_row_fraction or 0.0
    column_fraction = stat.max_column_fraction or 0.0
    line_fraction = max(row_fraction, column_fraction)
    if (
        stat.count >= config.min_cluster_size
        and line_fraction >= config.line_concentration_threshold
    ):
        orientation = "ROW" if row_fraction >= column_fraction else "COLUMN"
        results.append(
            _pattern(
                "LINE",
                stat.soft_bin,
                min(1.0, 0.55 + 0.45 * line_fraction),
                [
                    f"orientation={orientation}",
                    f"max_row_fraction={row_fraction:.3f}",
                    f"max_column_fraction={column_fraction:.3f}",
                ],
                {
                    "line_concentration_threshold":
                        config.line_concentration_threshold,
                },
                [
                    "Phase 2 line detection covers row/column concentration; "
                    "arbitrary diagonal scratch fitting is deferred."
                ],
            )
        )

    if not results:
        results.append(
            _pattern(
                "RANDOM",
                stat.soft_bin,
                max(0.30, 1.0 - cluster_ratio),
                [
                    f"edge_enrichment={(stat.edge.enrichment or 0.0):.3f}",
                    f"center_enrichment={(stat.center.enrichment or 0.0):.3f}",
                    f"cluster_ratio={cluster_ratio:.3f}",
                ],
                {
                    "enrichment_threshold": enrichment_threshold,
                    "cluster_ratio_threshold": config.cluster_ratio_threshold,
                },
                ["RANDOM means no Phase 2 deterministic pattern threshold was met."],
            )
        )

    return results


class AnalysisEngine:
    def analyze(
        self,
        dataset: WaferDataset,
        *,
        config: AnalysisConfig | None = None,
    ) -> AnalysisSummary:
        actual_config = config or AnalysisConfig()
        geometry = build_geometry(dataset.dies, actual_config)

        by_region: dict[str, list[DieRecord]] = {
            name: [] for name in _REGION_NAMES
        }
        by_bin: dict[int, list[DieRecord]] = defaultdict(list)
        by_bin_region: dict[int, Counter[str]] = defaultdict(Counter)

        for die in dataset.dies:
            if die.soft_bin is not None:
                by_bin[die.soft_bin].append(die)
            geo = geometry[(die.row, die.column)]
            for region in _region_membership(geo):
                by_region[region].append(die)
                if die.soft_bin is not None:
                    by_bin_region[die.soft_bin][region] += 1

        region_stats = {
            region: _region_metric(dies)
            for region, dies in by_region.items()
        }

        bin_stats: list[BinStat] = []
        spatial_by_bin: list[SpatialBinStat] = []
        total_tested = dataset.summary.tested_die
        fail_die = dataset.summary.fail_die

        for bin_record in sorted(dataset.bins, key=lambda item: item.bin):
            count = bin_record.count
            bin_stats.append(
                BinStat(
                    soft_bin=bin_record.bin,
                    char=bin_record.char,
                    description=bin_record.description,
                    count=count,
                    wafer_rate=_safe_rate(count, total_tested) or 0.0,
                    fail_share=(
                        _safe_rate(count, fail_die)
                        if "PASS" not in (bin_record.description or "").upper()
                        else None
                    ),
                )
            )

            bin_dies = by_bin.get(bin_record.bin, [])
            counts = by_bin_region[bin_record.bin]
            coordinates = {(die.row, die.column) for die in bin_dies}
            row_counts = Counter(die.row for die in bin_dies)
            column_counts = Counter(die.column for die in bin_dies)

            def metric(region: str) -> BinRegionMetric:
                return _bin_region_metric(
                    region_tested=region_stats[region].tested_die,
                    region_bin_count=counts[region],
                    whole_tested=total_tested,
                    whole_bin_count=count,
                )

            spatial_by_bin.append(
                SpatialBinStat(
                    soft_bin=bin_record.bin,
                    count=count,
                    center=metric("center"),
                    mid=metric("mid"),
                    edge=metric("edge"),
                    top=metric("top"),
                    bottom=metric("bottom"),
                    left=metric("left"),
                    right=metric("right"),
                    q1=metric("q1"),
                    q2=metric("q2"),
                    q3=metric("q3"),
                    q4=metric("q4"),
                    cluster=connected_components(
                        coordinates,
                        neighbor_mode=actual_config.neighbor_mode,
                    ),
                    max_row_fraction=(
                        max(row_counts.values()) / count if count and row_counts else None
                    ),
                    max_column_fraction=(
                        max(column_counts.values()) / count
                        if count and column_counts
                        else None
                    ),
                )
            )

        patterns: list[PatternResult] = []
        pass_bins = {
            item.bin
            for item in dataset.bins
            if "PASS" in (item.description or "").upper()
        } or {1}
        for stat in spatial_by_bin:
            if stat.soft_bin in pass_bins or stat.count == 0:
                continue
            patterns.extend(_detect_patterns(stat, actual_config))

        patterns.sort(key=lambda item: item.score, reverse=True)

        fail_bins = [
            item for item in bin_stats if item.soft_bin not in pass_bins and item.count > 0
        ]
        fail_bins.sort(key=lambda item: item.count, reverse=True)

        findings = [
            (
                f"Yield={dataset.summary.yield_:.4f}; "
                f"tested={dataset.summary.tested_die}, "
                f"pass={dataset.summary.pass_die}, fail={dataset.summary.fail_die}."
            )
            if dataset.summary.yield_ is not None
            else (
                f"Yield unavailable; tested={dataset.summary.tested_die}, "
                f"pass={dataset.summary.pass_die}, fail={dataset.summary.fail_die}."
            )
        ]
        if fail_bins:
            main = fail_bins[0]
            findings.append(
                f"Main fail bin is {main.soft_bin} ({main.description or 'N/A'}), "
                f"count={main.count}, fail_share={(main.fail_share or 0.0):.4f}."
            )
        if patterns:
            top = patterns[0]
            findings.append(
                f"Top deterministic pattern is {top.pattern} for Bin {top.soft_bin} "
                f"with score={top.score:.3f}."
            )

        limitations = [
            "Geometry uses tested-die bounding box normalization rather than physical wafer dimensions.",
            "Pattern scores are deterministic algorithm confidence, not root-cause confidence.",
            "Phase 2 LINE detection covers row/column concentration; arbitrary diagonal scratch fitting is deferred.",
        ]

        return AnalysisSummary(
            metadata=dataset.metadata,
            summary=dataset.summary,
            validation=[],
            config=actual_config,
            bin_stats=bin_stats,
            region_stats=region_stats,
            spatial_by_bin=spatial_by_bin,
            patterns=patterns,
            top_findings=findings,
            limitations=limitations,
        )
