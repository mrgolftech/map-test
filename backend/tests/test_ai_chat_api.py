import json

import app.services.ai_analysis_service as ai_analysis_module
import app.services.ai_chat_service as ai_chat_module
from app.ai.provider import AIProvider
from app.core.config import get_settings
from app.simulator.patterns import generate_pattern_dataset

REPORT = {
    "executive_summary": "主要失效 Bin 有局部聚集迹象，根因尚未确认。",
    "key_findings": [],
    "spatial_patterns": [],
    "possible_causes": [],
    "recommended_checks": [],
    "confidence": 0.7,
    "limitations": ["缺少工艺和探针维护记录。"],
}


class FixedProvider(AIProvider):
    def __init__(self, response: str):
        self.response = response
        self.prompts: list[str] = []

    def complete(self, *, system_prompt, user_prompt, max_tokens, temperature):
        if "citation_ids" in system_prompt:
            assert "only the supplied" in system_prompt
        self.prompts.append(user_prompt)
        assert max_tokens > 0
        assert temperature == 0.2
        return self.response

    def test_connection(self):
        pass


def configure_llm(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("LLM_API_KEY", "chat-secret")
    monkeypatch.setenv("LLM_MODEL", "chat-demo")
    get_settings.cache_clear()


def persist(client, *, lot="CHAT-LOT", wafer="01", scenario="PRODUCTION_PROFILE_COMPACT"):
    dataset = generate_pattern_dataset(scenario, seed=20260924, fail_count=322)
    dataset.metadata.product_id = "CHAT-DEMO"
    dataset.metadata.lot_id = lot
    dataset.metadata.wafer_id = wafer
    response = client.post(
        "/api/v1/analyses",
        json={
            "dataset": dataset.model_dump(mode="json", by_alias=True),
            "sources": [],
            "validation_issues": [],
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]["id"]


def save_report(client, monkeypatch, analysis_id):
    monkeypatch.setattr(
        ai_analysis_module,
        "create_provider",
        lambda _settings: FixedProvider(json.dumps(REPORT, ensure_ascii=False)),
    )
    response = client.post(f"/api/v1/analyses/{analysis_id}/ai")
    assert response.status_code == 200, response.text


def test_analysis_chat_requires_saved_report(client):
    analysis_id = persist(client)

    response = client.post(
        f"/api/v1/ai/chat/analyses/{analysis_id}",
        json={"question": "这片晶圆的主要问题是什么？"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "AI_REPORT_REQUIRED"


def test_analysis_chat_is_grounded_and_persisted(client, monkeypatch):
    configure_llm(monkeypatch)
    analysis_id = persist(client)
    save_report(client, monkeypatch, analysis_id)
    provider = FixedProvider(
        json.dumps(
            {
                "answer": "良率为 37.11%。",
                "citation_ids": ["summary.yield"],
                "insufficient_evidence": False,
                "limitations": [],
            },
            ensure_ascii=False,
        )
    )
    monkeypatch.setattr(ai_chat_module, "OpenAICompatibleProvider", lambda **_kwargs: provider)

    asked = client.post(
        f"/api/v1/ai/chat/analyses/{analysis_id}",
        json={"question": "这片晶圆良率是多少？"},
    )
    assert asked.status_code == 200, asked.text
    data = asked.json()["data"]
    assert len(data["messages"]) == 2
    assert data["messages"][0]["content"] == "这片晶圆良率是多少？"
    answer = data["messages"][1]
    assert answer["citations"] == [
        {
            "id": "summary.yield",
            "label": "Yield",
            "value": "37.11%",
            "analysis_id": None,
        }
    ]
    prompt = json.loads(provider.prompts[0])
    assert prompt["context"]["saved_ai_report"]["executive_summary"] == REPORT[
        "executive_summary"
    ]
    assert "dies" not in provider.prompts[0]
    restored = client.get(f"/api/v1/ai/chat/analyses/{analysis_id}")
    assert restored.status_code == 200
    assert restored.json()["data"]["messages"] == data["messages"]


def test_analysis_chat_accepts_single_string_limitation(client, monkeypatch):
    configure_llm(monkeypatch)
    analysis_id = persist(client)
    save_report(client, monkeypatch, analysis_id)
    provider = FixedProvider(
        json.dumps(
            {
                "answer": "良率为 37.11%。",
                "citation_ids": ["summary.yield"],
                "insufficient_evidence": False,
                "limitations": "该结论仅基于当前晶圆数据。",
            },
            ensure_ascii=False,
        )
    )
    monkeypatch.setattr(
        ai_chat_module, "OpenAICompatibleProvider", lambda **_kwargs: provider
    )

    response = client.post(
        f"/api/v1/ai/chat/analyses/{analysis_id}",
        json={"question": "这片晶圆良率是多少？"},
    )

    assert response.status_code == 200, response.text
    answer = response.json()["data"]["messages"][-1]
    assert answer["limitations"] == ["该结论仅基于当前晶圆数据。"]


def test_comparison_chat_cites_wafer_metrics_and_marks_invalid_citations(
    client, monkeypatch
):
    configure_llm(monkeypatch)
    ids = [persist(client, wafer=f"0{index}") for index in (1, 2)]
    invalid_provider = FixedProvider(
        json.dumps(
            {
                "answer": "沒有足夠數據判斷。",
                "citation_ids": ["made-up.metric"],
                "insufficient_evidence": False,
                "limitations": [],
            },
            ensure_ascii=False,
        )
    )
    monkeypatch.setattr(
        ai_chat_module,
        "OpenAICompatibleProvider",
        lambda **_kwargs: invalid_provider,
    )

    asked = client.post(
        "/api/v1/ai/chat/comparison",
        json={"analysis_ids": ids, "question": "兩片晶圓的模式有重複嗎？"},
    )
    assert asked.status_code == 200, asked.text
    messages = asked.json()["data"]["messages"]
    answer = messages[-1]
    assert answer["citations"] == []
    assert answer["insufficient_evidence"] is True
    assert "证据不足" in answer["content"]
    prompt = json.loads(invalid_provider.prompts[0])
    evidence_ids = {item["id"] for item in prompt["available_evidence"]}
    assert any(item.startswith(f"wafer.{ids[0]}.pattern.") for item in evidence_ids)

    restored = client.get(
        "/api/v1/ai/chat/comparison",
        params=[("analysis_ids", item) for item in reversed(ids)],
    )
    assert restored.status_code == 200
    assert restored.json()["data"]["messages"] == messages


def test_comparison_chat_caps_excessive_valid_citations(client, monkeypatch):
    configure_llm(monkeypatch)
    ids = [persist(client, wafer=f"0{index}") for index in (1, 2)]

    class VerboseCitationProvider(FixedProvider):
        def complete(self, *, system_prompt, user_prompt, max_tokens, temperature):
            prompt = json.loads(user_prompt)
            evidence_ids = [item["id"] for item in prompt["available_evidence"]]
            assert len(evidence_ids) >= 13
            self.response = json.dumps(
                {
                    "answer": "两片晶圆有多项指标可供比较。",
                    "citation_ids": evidence_ids[:15],
                    "insufficient_evidence": False,
                    "limitations": [],
                },
                ensure_ascii=False,
            )
            return super().complete(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )

    provider = VerboseCitationProvider("")
    monkeypatch.setattr(
        ai_chat_module, "OpenAICompatibleProvider", lambda **_kwargs: provider
    )

    response = client.post(
        "/api/v1/ai/chat/comparison",
        json={"analysis_ids": ids, "question": "比较这两片晶圆。"},
    )

    assert response.status_code == 200, response.text
    answer = response.json()["data"]["messages"][-1]
    assert len(answer["citations"]) == 12
    assert answer["insufficient_evidence"] is True
    assert "证据不足" in answer["content"]
    assert any("超过 12 项展示上限" in item for item in answer["limitations"])


def test_deleting_analysis_removes_related_chat_thread(client, monkeypatch):
    configure_llm(monkeypatch)
    analysis_id = persist(client)
    save_report(client, monkeypatch, analysis_id)
    provider = FixedProvider(
        json.dumps(
            {
                "answer": "良率见引用。",
                "citation_ids": ["summary.yield"],
                "insufficient_evidence": False,
                "limitations": [],
            },
            ensure_ascii=False,
        )
    )
    monkeypatch.setattr(ai_chat_module, "OpenAICompatibleProvider", lambda **_kwargs: provider)
    assert client.post(
        f"/api/v1/ai/chat/analyses/{analysis_id}",
        json={"question": "良率是多少？"},
    ).status_code == 200

    assert client.delete(f"/api/v1/analyses/{analysis_id}").status_code == 200
    assert client.get(f"/api/v1/ai/chat/analyses/{analysis_id}").status_code == 404
