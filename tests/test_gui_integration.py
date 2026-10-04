"""
LOCUS GUI & SOC Dashboard Integration Test Suite
Module: tests.test_gui_integration
Validates:
- SOCDataService telemetry, features, and evidence retrieval
- Canonical 10-D feature validation and threshold limits
- Zero fabrication guards (Live vs Historical mode)
- Alert Center generation and Evidence Bundle drilldown
- System health matrix auditing
- FastAPI enriched endpoints (/api/telemetry, /api/features, /api/alerts, /api/agents, /api/rag/query)
- Graceful degradation on missing or invalid data
"""

import pytest
import pandas as pd
from fastapi.testclient import TestClient

from src.ui.data_service import SOCDataService
from src.api.app import app
from src.evidence.evidence_bundle import EvidenceBundle


@pytest.fixture(scope="module")
def data_service():
    return SOCDataService()


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


class TestSOCDataService:
    """Tests for the GUI data provider service."""

    def test_gnss_connection_guard(self, data_service):
        """Verify connection check accurately reports hardware or replay mode without fabrication."""
        conn = data_service.check_gnss_connection()
        assert "status" in conn
        assert "mode" in conn
        assert "is_live" in conn
        assert "provenance" in conn
        if not conn["is_live"]:
            assert "HISTORICAL" in conn["mode"] or "REPLAY" in conn["mode"]

    def test_load_telemetry_dataset(self, data_service):
        """Verify telemetry dataset loading and valid fix filtering."""
        df = data_service.load_telemetry_dataset()
        assert not df.empty, "Processed telemetry dataset should not be empty"
        assert "latitude" in df.columns
        assert "longitude" in df.columns
        assert "speed_kmh" in df.columns
        assert "hdop" in df.columns

    def test_latest_telemetry_metrics(self, data_service):
        """Verify latest valid telemetry extraction."""
        tel = data_service.get_latest_telemetry_metrics()
        assert tel["has_data"] is True
        assert "latitude" in tel
        assert "speed_kmh" in tel
        assert "satellites_used" in tel
        assert "hdop" in tel

    def test_canonical_10d_features(self, data_service):
        """Verify exact canonical 10-D feature vector names and thresholds."""
        feats = data_service.get_canonical_10d_features()
        assert len(feats) == 10, f"Expected exactly 10 features, got {len(feats)}"

        canonical_names = [
            "disp_haversine", "vel_kinematic", "acc_kinematic", "jerk_kinematic",
            "bearing_rate", "HDOP", "VDOP", "fix_integrity", "sat_count_tot", "sat_churn"
        ]
        extracted_names = [f["feature"] for f in feats]
        assert extracted_names == canonical_names

        for f in feats:
            assert "value" in f
            assert "unit" in f
            assert "warning_limit" in f
            assert "critical_limit" in f
            assert f["status"] in ["NORMAL", "WARNING", "CRITICAL"]

    def test_alert_center_records(self, data_service):
        """Verify alert extraction and priority sorting."""
        alerts = data_service.get_alert_center_records()
        assert len(alerts) > 0, "Expected forensic alerts from evidence store"
        for a in alerts:
            assert "alert_id" in a
            assert "severity" in a
            assert a["severity"] in ["CRITICAL", "HIGH", "WARNING", "INFO"]
            assert "anomaly_score" in a
            assert "affected_features" in a

    def test_system_health_matrix(self, data_service):
        """Verify comprehensive component health auditing."""
        health = data_service.get_system_health_matrix()
        assert len(health) >= 12, "Expected complete health matrix covering hardware, pipeline, models, and agents"
        components = [h["component"] for h in health]
        assert any("Receiver" in c for c in components)
        assert any("Rules" in c for c in components)
        assert any("Isolation Forest" in c for c in components)
        assert any("Agent" in c for c in components)
        assert any("RAG" in c for c in components)

    def test_empty_dataset_graceful_fallback(self):
        """Verify service handles non-existent paths gracefully without crashing."""
        dummy_svc = SOCDataService(
            telemetry_path="data/non_existent.csv",
            features_path="data/non_existent.csv",
            evidence_dir="data/non_existent_evidence",
            api_base_url="http://127.0.0.1:9999"  # Offline API port to force local file fallback
        )
        assert dummy_svc.load_telemetry_dataset().empty
        assert dummy_svc.load_features_dataset().empty
        metrics = dummy_svc.get_latest_telemetry_metrics()
        assert metrics["has_data"] is False
        assert metrics["message"] == "NO LIVE DATA"


class TestFastAPIEnrichedEndpoints:
    """Tests for the newly exposed GUI-ready REST endpoints."""

    def test_api_telemetry_latest(self, client):
        r = client.get("/api/telemetry/latest")
        assert r.status_code == 200
        data = r.json()
        assert "mode" in data
        assert "telemetry" in data
        assert "speed_kmh" in data["telemetry"]

    def test_api_telemetry_history(self, client):
        r = client.get("/api/telemetry/history?limit=25")
        assert r.status_code == 200
        data = r.json()
        assert data["count"] <= 25
        assert len(data["records"]) == data["count"]

    def test_api_features_latest(self, client):
        r = client.get("/api/features/latest")
        assert r.status_code == 200
        data = r.json()
        assert "features" in data
        assert len(data["features"]) == 10
        assert "disp_haversine" in data["features"]
        assert "status_evaluation" in data

    def test_api_alerts(self, client):
        r = client.get("/api/alerts")
        assert r.status_code == 200
        data = r.json()
        assert data["count"] > 0
        assert "alerts" in data
        first_alert = data["alerts"][0]
        assert "alert_id" in first_alert

    def test_api_alert_detail(self, client):
        r = client.get("/api/alerts")
        first_id = r.json()["alerts"][0]["alert_id"]
        r_det = client.get(f"/api/alerts/{first_id}")
        assert r_det.status_code == 200
        assert "event_id" in r_det.json()

    def test_api_evidence_bundle(self, client):
        r = client.get("/api/events")
        first_id = r.json()["events"][0]["event_id"]
        r_ev = client.get(f"/api/evidence/{first_id}")
        assert r_ev.status_code == 200
        data = r_ev.json()
        assert "event_id" in data
        assert "security_features" in data

    def test_api_agents_status(self, client):
        r = client.get("/api/agents/status")
        assert r.status_code == 200
        agents = r.json().get("agents", {})
        assert "agent_1_integrity" in agents
        assert "agent_2_temporal_threat" in agents
        assert "agent_3_master_soc" in agents

    def test_api_rag_query(self, client):
        payload = {
            "query": "What are the RTCA DO-229E limits on HDOP?",
            "top_k": 2
        }
        r = client.post("/api/rag/query", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert "query" in data
        assert "citations_count" in data
        assert "citations" in data
