"""
LOCUS Security RAG Subsystem — Unit & Integration Test Suite

Module: tests.test_rag
Validates:
- Document ingestion & semantic chunking
- SQLite vector database & embedding creation
- Context retrieval with source metadata
- Insufficient context fallback (no unsupported claims / hallucination)
- Read-only sensor data immutability guarantee
- Agent 3 (Master SOC Agent) RAG deliberation integration
"""

import os
import shutil
import tempfile
import pytest
from typing import Dict, Any

from src.evidence.evidence_bundle import EvidenceBundle
from src.agents.integrity_agent import GNSSIntegrityAgent
from src.agents.temporal_threat_agent import TemporalThreatAgent
from src.agents.master_soc_agent import MasterSOCAgent
from src.rag.document_ingestion import DocumentIngester, DocumentChunk
from src.rag.retriever import VectorStore, ContextRetriever, RetrievalOutput
from src.rag.rag_engine import SecurityRAGEngine


@pytest.fixture(scope="module")
def sample_evidence_bundle() -> EvidenceBundle:
    """Provides a sample EvidenceBundle representing a spoofing velocity breach."""
    return EvidenceBundle(
        event_id="test_evt_rag_001",
        timestamp_utc="2026-10-04T12:00:00.000Z",
        timestamp_pc="2026-10-04T17:30:00.000",
        session_id=1,
        epoch_id=100,
        location={"latitude": 23.1043, "longitude": 72.5925, "altitude_m": 66.0},
        security_features={
            "disp_haversine": 45.2,
            "vel_kinematic": 45.2,
            "acc_kinematic": 12.5,
            "jerk_kinematic": 28.0,
            "bearing_rate": 85.0,
            "HDOP": 1.2,
            "VDOP": 1.4,
            "fix_integrity": 0.15,
            "sat_count_tot": 18.0,
            "sat_churn": 0.55
        },
        physical_rules={
            "triggered_count": 3,
            "max_severity": "CRITICAL",
            "triggered_rules": [
                {"rule_name": "RULE_MAX_ACCELERATION", "diagnostic": "acc 12.5 m/s2 exceeds max physical limit"},
                {"rule_name": "RULE_MAX_JERK", "diagnostic": "jerk 28.0 m/s3 exceeds max physical limit"}
            ]
        },
        isolation_forest={
            "anomaly_score": 0.88,
            "is_anomaly": True
        },
        xgboost={
            "status": "UNFITTED_PENDING_LABELLED_SCENARIOS"
        },
        temporal_model={
            "reconstruction_error": 8.45,
            "error_threshold": 2.10,
            "is_anomaly": True
        },
        data_quality={
            "fix_quality": 1,
            "satellites_used": 18,
            "hdop": 1.2,
            "data_quality_flag": "VALID"
        },
        model_versions={
            "isolation_forest": "v1.1",
            "temporal_model": "v1.1",
            "xgboost": "v1.1"
        }
    )


class TestDocumentIngestion:
    """Tests for document parsing, metadata extraction, and chunking."""

    def test_ingest_knowledge_base_directory(self):
        ingester = DocumentIngester(max_chunk_size=800, overlap_size=150)
        chunks = ingester.ingest_directory("knowledge_base")
        assert len(chunks) > 0, "Ingestion should produce chunks from knowledge_base/"

        # Verify all 8 core documents were ingested
        doc_names = set(c.doc_name for c in chunks)
        expected_docs = {
            "gnss_fundamentals.md",
            "gnss_integrity_raim.md",
            "gnss_spoofing.md",
            "gnss_jamming_rfi.md",
            "navigation_quality_dop.md",
            "satellite_behaviour_churn.md",
            "anomaly_detection_principles.md",
            "security_concepts_mitre.md"
        }
        for doc in expected_docs:
            assert doc in doc_names, f"Expected {doc} to be ingested into RAG knowledge base"

    def test_chunk_metadata_and_authorities(self):
        ingester = DocumentIngester()
        chunks = ingester.ingest_file("knowledge_base/gnss_integrity_raim.md")
        assert len(chunks) >= 2
        for chunk in chunks:
            assert chunk.title != ""
            assert chunk.section_title != ""
            assert any("RTCA DO-229E" in auth or "ICAO" in auth for auth in chunk.standard_authorities)
            assert len(chunk.tags) > 0


class TestVectorStoreAndRetrieval:
    """Tests for vector storage, similarity search, and grounding."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_vector_store.db")
        self.vector_store = VectorStore(db_path=self.db_path)
        ingester = DocumentIngester()
        chunks = ingester.ingest_directory("knowledge_base")
        self.vector_store.index_chunks(chunks)
        self.retriever = ContextRetriever(self.vector_store, min_similarity=0.12)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_vector_store_indexing(self):
        count = self.vector_store.count()
        assert count > 10, f"Expected more than 10 chunks indexed, got {count}"

    def test_semantic_retrieval_spoofing(self):
        out: RetrievalOutput = self.retriever.retrieve("GNSS spoofing false signal injection lift-off velocity discrepancy", top_k=3)
        assert out.has_sufficient_context is True
        assert len(out.retrieved_contexts) > 0
        top_match = out.retrieved_contexts[0]
        assert "spoofing" in top_match.doc_name.lower() or "spoofing" in top_match.text.lower()
        assert any("CISA" in a or "ICAO" in a or "MITRE" in a for a in out.top_authorities)
        assert top_match.similarity_score > 0.15

    def test_semantic_retrieval_jamming(self):
        out: RetrievalOutput = self.retriever.retrieve("carrier to noise ratio plunge C/N0 jamming RFI attenuation", top_k=3)
        assert out.has_sufficient_context is True
        top_match = out.retrieved_contexts[0]
        assert "jamming" in top_match.doc_name.lower() or "c/n0" in top_match.text.lower()

    def test_insufficient_context_fallback(self):
        """Verify Requirement 9: explicit insufficient context indication for out-of-domain queries."""
        out: RetrievalOutput = self.retriever.retrieve("baking chocolate chip cookies recipe oven temperature dough", top_k=3)
        assert out.has_sufficient_context is False
        assert out.insufficient_context_message is not None
        assert "Insufficient knowledge context" in out.insufficient_context_message


class TestSecurityRAGEngine:
    """Tests for the high-level SecurityRAGEngine coordinator."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "engine_vectors.db")
        self.rag_engine = SecurityRAGEngine(
            knowledge_base_dir="knowledge_base",
            db_path=self.db_path,
            auto_index=True
        )

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_rag_engine_query(self):
        res = self.rag_engine.query("What are the horizontal dilution of precision thresholds for navigation?")
        assert res["has_sufficient_context"] is True
        assert len(res["citations"]) > 0
        assert any("DO-229E" in auth or "NMEA" in auth or "ICAO" in auth for auth in res["regulatory_authorities"])

    def test_ground_soc_evidence_non_mutation(self, sample_evidence_bundle):
        """Verify Requirement 8: RAG layer must never mutate or overwrite telemetry values."""
        # Capture pre-grounding snapshot
        original_disp = sample_evidence_bundle.security_features["disp_haversine"]
        original_acc = sample_evidence_bundle.security_features["acc_kinematic"]
        original_hdop = sample_evidence_bundle.security_features["HDOP"]

        grounding = self.rag_engine.ground_soc_evidence(sample_evidence_bundle)
        
        assert grounding["is_grounded"] is True
        assert grounding["immutable_sensor_data_verified"] is True
        assert len(grounding["regulatory_standards"]) > 0
        assert len(grounding["citations"]) > 0

        # Verify telemetry values are identical
        assert sample_evidence_bundle.security_features["disp_haversine"] == original_disp
        assert sample_evidence_bundle.security_features["acc_kinematic"] == original_acc
        assert sample_evidence_bundle.security_features["HDOP"] == original_hdop

    def test_agent3_integration(self, sample_evidence_bundle):
        """Verify Agent 3 deliberation receives grounded RAG regulatory citations."""
        agent1 = GNSSIntegrityAgent()
        agent2 = TemporalThreatAgent()
        master_agent = MasterSOCAgent()

        a1_res = agent1.assess(sample_evidence_bundle)
        a2_res = agent2.assess(sample_evidence_bundle)

        final_verdict = self.rag_engine.deliberate_with_agent3(
            master_agent=master_agent,
            bundle=sample_evidence_bundle,
            integrity_output=a1_res,
            temporal_output=a2_res
        )

        assert final_verdict.status == "CONFIRMED_ATTACK"
        assert final_verdict.risk_level == "DEFCON_1_CRITICAL"
        assert "rag_context" in final_verdict.agent_findings
        rag_ctx = final_verdict.agent_findings["rag_context"]
        assert rag_ctx["is_grounded"] is True
        assert len(rag_ctx["regulatory_standards"]) > 0
        assert "Regulatory Citation" in final_verdict.summary
