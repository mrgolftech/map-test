import json

from app.schemas.analysis import AnalysisSummary


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
    fail_bins = [
        item
        for item in analysis.bin_stats
        if item.fail_share is not None and item.count > 0
    ]
    top_fail_bins = sorted(
        fail_bins,
        key=lambda item: item.fail_share or 0.0,
        reverse=True,
    )[:8]
    top_ids = {item.soft_bin for item in top_fail_bins}

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
            key: value.model_dump(mode="json")
            for key, value in analysis.region_stats.items()
        },
        "spatial_by_top_fail_bin": spatial,
        "patterns": [
            item.model_dump(mode="json")
            for item in analysis.patterns[:12]
        ],
        "deterministic_findings": [
            item.model_dump(mode="json")
            for item in analysis.top_findings
        ],
        "analysis_limitations": analysis.limitations,
    }


def build_user_prompt(analysis: AnalysisSummary) -> str:
    payload = compact_analysis_payload(analysis)
    return (
        "以下 JSON 是平台已经完成的确定性分析结果。"
        "请只基于这些数据生成结构化诊断解释，不要重新计算或补造事实。\n"
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    )
