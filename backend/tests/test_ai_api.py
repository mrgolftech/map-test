import json

import app.services.ai_analysis_service as ai_service_module
from app.ai.provider import AIProvider
from app.core.config import get_settings
from app.simulator.patterns import generate_pattern_dataset

REPORT = {
    "executive_summary": "该晶圆存在明确的边缘失效特征，需结合确定性统计继续验证。",
    "key_findings": [
        {
            "kind": "FACT",
            "title": "良率事实",
            "detail": "良率与失效数量来自平台确定性统计。",
            "evidence": ["AnalysisSummary.summary"],
        },
        {
            "kind": "JUDGMENT",
            "title": "空间判断",
            "detail": "主要 Fail Bin 的边缘富集与算法模式结果一致。",
            "evidence": ["edge_enrichment", "patterns"],
        },
    ],
    "spatial_patterns": [
        {
            "kind": "JUDGMENT",
            "title": "Edge pattern",
            "detail": "确定性模式识别给出了 EDGE 证据。",
            "evidence": ["pattern=EDGE"],
        }
    ],
    "possible_causes": [
        {
            "kind": "HYPOTHESIS",
            "title": "边缘工艺均匀性",
            "detail": "可能与边缘区域工艺均匀性有关，尚未确认。",
            "rationale": "边缘富集只说明空间相关性，不能直接确认工艺根因。",
        }
    ],
    "recommended_checks": [
        {
            "kind": "RECOMMENDATION",
            "title": "复核相邻 Wafer",
            "action": "对同 Lot 相邻 Wafer 的同一 Bin 做边缘富集对比。",
            "expected_evidence": "若同类边缘模式重复出现，可提高批次级异常假设的可信度。",
        }
    ],
    "confidence": 0.78,
    "limitations": ["未提供工艺参数，无法确认根因。"],
}


class FakeProvider(AIProvider):
    def __init__(self, content: str | None = None) -> None:
        self.content = content or json.dumps(REPORT, ensure_ascii=False)
        self.tested = False

    def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        assert "source of truth" in system_prompt
        assert "deterministic_findings" in user_prompt
        assert "dies" not in user_prompt
        assert max_tokens > 0
        assert temperature == 0.2
        return self.content

    def test_connection(self) -> None:
        self.tested = True


def configure_llm(monkeypatch) -> None:
    monkeypatch.setenv("LLM_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("LLM_API_KEY", "server-only-secret")
    monkeypatch.setenv("LLM_MODEL", "demo-model")
    get_settings.cache_clear()


def persist(client) -> str:
    dataset = generate_pattern_dataset("EDGE", fail_count=48)
    dataset.metadata.product_id = "AI-DEMO"
    dataset.metadata.lot_id = "LOT-AI"
    dataset.metadata.wafer_id = "01"
    response = client.post(
        "/api/v1/analyses",
        json={
            "dataset": dataset.model_dump(mode="json", by_alias=True),
            "sources": [],
            "validation_issues": [],
        },
    )
    assert response.status_code == 200
    return response.json()["data"]["id"]


def test_ai_config_never_exposes_api_key(client, monkeypatch):
    configure_llm(monkeypatch)

    response = client.get("/api/v1/settings/llm")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data == {
        "configured": True,
        "base_url": "https://example.test/v1",
        "model": "demo-model",
        "api_key_configured": True,
    }
    assert "server-only-secret" not in response.text


def test_ai_analyze_uses_persisted_analysis_summary(client, monkeypatch):
    configure_llm(monkeypatch)
    analysis_id = persist(client)
    fake = FakeProvider()
    monkeypatch.setattr(
        ai_service_module,
        "create_provider",
        lambda _settings: fake,
    )

    response = client.post(
        "/api/v1/ai/analyze",
        json={"analysis_id": analysis_id},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["analysis_id"] == analysis_id
    assert data["model"] == "demo-model"
    assert data["report"]["possible_causes"][0]["kind"] == "HYPOTHESIS"
    assert data["report"]["recommended_checks"][0]["kind"] == "RECOMMENDATION"

    restored = client.get(f"/api/v1/analyses/{analysis_id}")
    assert restored.status_code == 200
    detail = restored.json()["data"]
    assert detail["ai_model"] == "demo-model"
    assert detail["ai_generated_at"] is not None
    assert detail["ai_report"] == data["report"]


def test_ai_invalid_schema_is_explicit_error(client, monkeypatch):
    configure_llm(monkeypatch)
    analysis_id = persist(client)
    monkeypatch.setattr(
        ai_service_module,
        "create_provider",
        lambda _settings: FakeProvider('{"executive_summary":"incomplete"}'),
    )

    response = client.post(f"/api/v1/analyses/{analysis_id}/ai")

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "LLM_SCHEMA_INVALID"


def test_ai_missing_required_section_does_not_discard_saved_analysis(client, monkeypatch):
    configure_llm(monkeypatch)
    analysis_id = persist(client)
    incomplete = {key: value for key, value in REPORT.items() if key != "possible_causes"}
    monkeypatch.setattr(
        ai_service_module,
        "create_provider",
        lambda _settings: FakeProvider(json.dumps(incomplete)),
    )

    response = client.post(f"/api/v1/analyses/{analysis_id}/ai")

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "LLM_SCHEMA_INVALID"
    assert client.get(f"/api/v1/analyses/{analysis_id}").status_code == 200


def test_ai_accepts_markdown_json_fence_and_rejects_invalid_json(client, monkeypatch):
    configure_llm(monkeypatch)
    analysis_id = persist(client)
    fenced = "```json\n" + json.dumps(REPORT) + "\n```"
    monkeypatch.setattr(
        ai_service_module, "create_provider", lambda _settings: FakeProvider(fenced)
    )
    assert client.post(f"/api/v1/analyses/{analysis_id}/ai").status_code == 200

    monkeypatch.setattr(
        ai_service_module, "create_provider", lambda _settings: FakeProvider("{broken")
    )
    failed = client.post(f"/api/v1/analyses/{analysis_id}/ai")
    assert failed.status_code == 502
    assert failed.json()["error"]["code"] == "LLM_SCHEMA_INVALID"
    assert client.get(f"/api/v1/analyses/{analysis_id}").json()["data"]["ai_report"] is not None


def test_ai_unconfigured_degrades_without_affecting_analysis(client):
    analysis_id = persist(client)

    response = client.post(f"/api/v1/analyses/{analysis_id}/ai")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "LLM_NOT_CONFIGURED"

    detail = client.get(f"/api/v1/analyses/{analysis_id}")
    assert detail.status_code == 200
