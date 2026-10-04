"""
LOCUS Final Security Query System — Unit & Integration Test Suite

Module: tests.test_query_system
Validates:
- Event enumeration and Evidence Bundle loading
- Complete response schema enforcement (all required keys present)
- Handling of all natural language example query intents
- Zero fabrication and insufficient evidence fallback
- FastAPI REST API endpoints (/api/health, /api/events, /api/query, /api/soc/deliberate)
"""

import pytest
from fastapi.testclient import TestClient

from src.query.query_processor import SecurityQueryProcessor
from src.evidence.evidence_bundle import EvidenceBundle
from src.api.app import app


@pytest.fixture(scope="module")
def processor():
    return SecurityQueryProcessor()


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


class TestSecurityQueryProcessor:
    """Tests for the query processor and explainability pipeline."""

    def test_list_available_events(self, processor):
        events = processor.list_available_events()
        assert len(events) > 0, "Expected evidence events in data/evidence/"
        for ev in events:
            assert "event_id" in ev
            assert "timestamp_utc" in ev

    def test_load_event(self, processor):
        events = processor.list_available_events()
        assert len(events) > 0
        first_id = events[0]["event_id"]
        bundle = processor.load_event(first_id)
        assert bundle is not None
        assert isinstance(bundle, EvidenceBundle)
        assert bundle.event_id == first_id
        assert len(bundle.security_features) >= 10

    def test_response_schema_completeness(self, processor):
        """Verify the final response contains ALL mandated fields."""
        events = processor.list_available_events()
        first_id = events[0]["event_id"]
        
        res = processor.process_query("Why was this event flagged?", event_id=first_id)

        # Mandatory fields check
        required_fields = [
            "event",
            "current_status",
            "risk_level",
            "confidence",
            "evidence",
            "feature_values",
            "model_outputs",
            "agent_findings",
            "rag_sources",
            "explanation",
            "recommended_next_action"
        ]
        for field in required_fields:
            assert field in res, f"Mandatory field '{field}' missing from SOC query response."

        assert isinstance(res["recommended_next_action"], list)
        assert isinstance(res["feature_values"], dict)
        assert isinstance(res["model_outputs"], dict)
        assert len(res["explanation"]) > 0

    def test_example_queries_execution(self, processor):
        """Verify each example query produces a tailored, non-empty explainable response."""
        events = processor.list_available_events()
        first_id = events[0]["event_id"]

        queries = [
            "Why was this event flagged?",
            "What features caused the anomaly?",
            "Is the anomaly persistent?",
            "Show me the evidence behind this alert.",
            "What did the temporal model detect?",
            "Explain the navigation-quality degradation."
        ]

        for q in queries:
            res = processor.process_query(q, event_id=first_id)
            assert res["current_status"] in ["NOMINAL", "TRANSIENT_NOISE", "SUSPECTED_INTERFERENCE", "CONFIRMED_ATTACK"]
            assert "DEFCON" in res["risk_level"]
            assert len(res["explanation"]) > 20
            # Ensure explanation answers the prompt
            assert not res["explanation"].startswith("Error")

    def test_insufficient_evidence_fallback(self):
        """Verify graceful fallback with no hallucinations when event is not found."""
        proc = SecurityQueryProcessor(evidence_dir="non_existent_directory")
        res = proc.process_query("Why was this flagged?", event_id="non_existent_evt")
        assert res["event"] is None
        assert "Insufficient evidence" in res["explanation"]


class TestFastAPIBackend:
    """Tests for the REST API endpoints."""

    def test_root_endpoint(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "OPERATIONAL"

    def test_health_endpoint(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "HEALTHY"
        assert data["total_available_events"] > 0
        assert data["rag_vector_store_chunks"] > 0

    def test_list_events_endpoint(self, client):
        resp = client.get("/api/events")
        assert resp.status_code == 200
        data = resp.json()
        assert "events" in data
        assert data["total"] > 0

    def test_get_event_detail_endpoint(self, client):
        events_resp = client.get("/api/events")
        first_id = events_resp.json()["events"][0]["event_id"]
        
        detail_resp = client.get(f"/api/events/{first_id}")
        assert detail_resp.status_code == 200
        data = detail_resp.json()
        assert data["event_id"] == first_id
        assert "security_features" in data
        assert "physical_rules" in data

    def test_query_endpoint(self, client):
        payload = {
            "query": "What did the temporal model detect?",
            "event_id": "evt_4_220"
        }
        resp = client.post("/api/query", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "explanation" in data
        assert "current_status" in data
        assert "risk_level" in data
        assert "recommended_next_action" in data

    def test_deliberate_endpoint(self, client):
        payload = {"event_id": "evt_4_220"}
        resp = client.post("/api/soc/deliberate", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "agent_findings" in data
        assert "rag_sources" in data
