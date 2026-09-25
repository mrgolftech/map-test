import json

from app.schemas.analysis import AnalysisSummary
from app.schemas.comparison import ComparisonData

SYSTEM_PROMPT = """You are the explanation layer of a semiconductor wafer analysis platform.

Strict rules:
1. Deterministic calculations supplied by the platform are the source of truth.
2. Never invent die counts, yield, Bin rates, enrichment, cluster metrics,
   patterns, tester data, or metadata.
3. Never convert a possible cause into a confirmed root cause.
4. Clearly separate FACT, JUDGMENT, HYPOTHESIS, and RECOMMENDATION.
5. FACT may only restate supplied deterministic facts.
6. JUDGMENT may only explain supplied deterministic pattern/evidence results.
7. HYPOTHESIS must be explicitly framed as unconfirmed and testable.
8. RECOMMENDATION must be a concrete verification action.
9. Return JSON only. No markdown fences or prose outside JSON.
10. Write the report in concise professional Chinese.
11. Keep the JSON compact: at most four key findings, four spatial patterns,
    four possible causes, and four recommended checks. Avoid long repeated evidence.
12. If lot comparison facts are supplied, explain the yield trend and outlier
    with the wafer-level pattern evidence. Compare the main Fail Bin cluster
    ratio across wafers explicitly when supplied. Do not claim a confirmed cause.
13. Cluster size and quadrant enrichment are separate aggregate statistics.
    Never locate the largest cluster inside a quadrant unless its coordinates
    are explicitly supplied; these inputs do not include cluster coordinates.
14. Use the following metric definitions exactly:
    - Geometry is derived from the tested-die row/column bounding box. The
      bounding-box center and half-widths normalize x/y; radius is hypot(x, y)
      divided by the maximum radius among tested dies. It is not calibrated to
      physical wafer dimensions, notch orientation, or an edge-exclusion zone.
    - Radial regions use analysis_config.center_radius and edge_radius:
      center is radius < center_radius; mid is center_radius <= radius <
      edge_radius; edge is radius >= edge_radius. Other regions are top/bottom,
      left/right, and Q1-Q4 from normalized coordinate signs.
    - For a Bin and region, region_rate = bin_die_in_region / tested_die_in_region;
      whole_rate = bin_die_on_wafer / total_tested_die; enrichment =
      region_rate / whole_rate. Enrichment 1 means the Bin's share matches the
      wafer-wide share; >1 means over-representation, not statistical
      significance or causation. Do not confuse fail_rate with Bin enrichment.
    - EDGE and CENTER require enrichment >= enrichment_threshold. RING requires
      mid enrichment >= enrichment_threshold and both edge and center
      enrichment < 1.20. TOP/BOTTOM/LEFT/RIGHT require target enrichment >=
      directional_enrichment_threshold and opposite enrichment <= 1.10.
      QUADRANT requires quadrant enrichment >= directional_enrichment_threshold
      and quadrant Bin count >= min_cluster_size.
    - LOCALIZED_CLUSTER uses connected components with neighbor_mode (4 or 8).
      It requires largest_component >= min_cluster_size and
      cluster_ratio >= cluster_ratio_threshold. cluster_ratio is largest
      component size / total dies in that Bin. It does not encode physical
      distance, process causality, or the component's quadrant.
    - LINE means row/column concentration: the larger of max_row_fraction and
      max_column_fraction meets line_concentration_threshold, with at least
      min_cluster_size Bin dies. Arbitrary diagonal scratch fitting is not
      implemented.
    - RANDOM means no implemented deterministic pattern threshold was met; it
      does not prove that the failures are statistically random.
15. Pattern scores are deterministic rule scores, not probabilities, calibrated
    confidence, or root-cause confidence. Do not interpret the report's
    confidence field as a validated probability; state limitations where useful.
16. Treat small Bin counts cautiously. Do not call a weak enrichment a stable
    pattern, and do not infer a physical wafer-edge defect from normalized
    bounding-box geometry alone.

Return exactly this shape:
{
  "executive_summary": "string",
  "key_findings": [
    {"kind": "FACT|JUDGMENT", "title": "string", "detail": "string", "evidence": ["string"]}
  ],
  "spatial_patterns": [
    {"kind": "JUDGMENT", "title": "string", "detail": "string", "evidence": ["string"]}
  ],
  "possible_causes": [
    {"kind": "HYPOTHESIS", "title": "string", "detail": "string", "rationale": "string"}
  ],
  "recommended_checks": [
    {
      "kind": "RECOMMENDATION",
      "title": "string",
      "action": "string",
      "expected_evidence": "string|null"
    }
  ],
  "confidence": 0.0,
  "limitations": ["string"]
}
"""


def compact_analysis_payload(analysis: AnalysisSummary) -> dict[str, object]:
    bin_counts = {item.soft_bin: item.count for item in analysis.bin_stats}
    fail_bins = [
        item for item in analysis.bin_stats if item.fail_share is not None and item.count > 0
    ]
    ranked_fail_bins = sorted(
        fail_bins,
        key=lambda item: item.fail_share or 0.0,
        reverse=True,
    )
    top_fail_bins = ranked_fail_bins[:8]
    significant_patterns = sorted(
        (
            item
            for item in analysis.patterns
            if item.pattern != "RANDOM"
            and item.soft_bin is not None
            and bin_counts.get(item.soft_bin, 0) >= max(4, int(analysis.summary.fail_die * 0.003))
        ),
        key=lambda item: (-bin_counts.get(item.soft_bin or -1, 0), -item.score),
    )
    priority_bin_ids = {item.soft_bin for item in significant_patterns}
    top_fail_bins.extend(item for item in ranked_fail_bins[8:] if item.soft_bin in priority_bin_ids)
    top_fail_bins = top_fail_bins[:10]
    top_ids = {item.soft_bin for item in top_fail_bins}
    selected_patterns = significant_patterns[:10]
    selected_patterns.extend(
        item
        for item in analysis.patterns
        if item.pattern == "RANDOM"
        and item.soft_bin in top_ids
        and item.soft_bin is not None
        and bin_counts.get(item.soft_bin, 0) >= analysis.summary.fail_die * 0.03
    )
    selected_patterns = selected_patterns[:12]

    spatial = []
    for item in analysis.spatial_by_bin:
        if item.soft_bin not in top_ids:
            continue
        spatial.append(
            {
                "soft_bin": item.soft_bin,
                "count": item.count,
                "edge_enrichment": item.edge.enrichment,
                "center_enrichment": item.center.enrichment,
                "top_enrichment": item.top.enrichment,
                "bottom_enrichment": item.bottom.enrichment,
                "left_enrichment": item.left.enrichment,
                "right_enrichment": item.right.enrichment,
                "q1_enrichment": item.q1.enrichment,
                "q2_enrichment": item.q2.enrichment,
                "q3_enrichment": item.q3.enrichment,
                "q4_enrichment": item.q4.enrichment,
                "cluster_ratio": item.cluster.cluster_ratio,
                "largest_component": item.cluster.largest_component,
                "max_row_fraction": item.max_row_fraction,
                "max_column_fraction": item.max_column_fraction,
            }
        )

    return {
        "metadata": analysis.metadata.model_dump(mode="json"),
        "summary": analysis.summary.model_dump(mode="json", by_alias=True),
        "analysis_config": analysis.config.model_dump(mode="json"),
        "top_fail_bins": [
            {
                "soft_bin": item.soft_bin,
                "char": item.char,
                "description": item.description,
                "count": item.count,
                "wafer_rate": item.wafer_rate,
                "fail_share": item.fail_share,
            }
            for item in top_fail_bins
        ],
        "region_stats": {
            key: value.model_dump(mode="json") for key, value in analysis.region_stats.items()
        },
        "spatial_by_top_fail_bin": spatial,
        "patterns": [item.model_dump(mode="json") for item in selected_patterns],
        "deterministic_findings": [item.model_dump(mode="json") for item in analysis.top_findings],
        "analysis_limitations": analysis.limitations,
    }


def build_user_prompt(analysis: AnalysisSummary, lot: ComparisonData | None = None) -> str:
    payload = compact_analysis_payload(analysis)
    if lot is not None:
        payload["lot_comparison"] = {
            "lot_id": lot.lot_id,
            "wafer_count": lot.yield_stats.wafer_count,
            "yield_trend": [
                point.model_dump(mode="json", by_alias=True) for point in lot.yield_trend
            ],
            "wafer_evidence": [
                {
                    "wafer_id": wafer.wafer_id,
                    "yield": wafer.yield_,
                    "fail_die": wafer.fail_die,
                    "main_fail_bin": wafer.main_fail_bin,
                    "main_pattern": wafer.main_pattern,
                    "main_bin_cluster_ratio": wafer.cluster_ratio,
                    "is_outlier": wafer.is_outlier,
                }
                for wafer in lot.wafers
            ],
            "limitations": lot.limitations,
        }
    return (
        "以下 JSON 是平台已经完成的确定性分析结果。"
        "请只基于这些数据生成结构化诊断解释，不要重新计算或补造事实。\n"
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    )
