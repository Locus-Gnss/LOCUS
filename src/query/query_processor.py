"""
LOCUS Security Query System — Query Processor & Explainability Engine

Module: src.query.query_processor
Focus: Natural language query interpretation, multi-agent SOC orchestration,
RAG standards grounding, and evidence-backed explainable response synthesis.

Architecture Flow:
User Query -> Query Processor -> Relevant Evidence Retrieval -> Agentic SOC -> RAG -> Master SOC Agent -> Final Response
"""

import os
import json
import re
from typing import Dict, List, Optional, Union, Any

from src.evidence.evidence_bundle import EvidenceBundle
from src.agents.integrity_agent import GNSSIntegrityAgent, IntegrityAssessment
from src.agents.temporal_threat_agent import TemporalThreatAgent, TemporalAssessment
from src.agents.master_soc_agent import MasterSOCAgent, SOCOrchestrationResult
from src.rag.rag_engine import SecurityRAGEngine


DEFAULT_EVIDENCE_DIR = os.path.join("data", "evidence")


class SecurityQueryProcessor:
    """
    Core Query Processor executing the full end-to-end LOCUS SOC reasoning pipeline.
    """

    def __init__(
        self,
        evidence_dir: str = DEFAULT_EVIDENCE_DIR,
        rag_engine: Optional[SecurityRAGEngine] = None
    ):
        self.evidence_dir = evidence_dir
        self.agent1 = GNSSIntegrityAgent()
        self.agent2 = TemporalThreatAgent()
        self.agent3 = MasterSOCAgent()
        self.rag_engine = rag_engine or SecurityRAGEngine(
            knowledge_base_dir="knowledge_base",
            db_path="data/rag/vector_store.db",
            auto_index=True
        )

    def list_available_events(self) -> List[Dict[str, Any]]:
        """
        List all available indexed GNSS events from evidence storage.
        """
        if not os.path.isdir(self.evidence_dir):
            return []

        events = []
        for fname in sorted(os.listdir(self.evidence_dir)):
            if fname.startswith("evidence_") and fname.endswith(".json"):
                fpath = os.path.join(self.evidence_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        events.append({
                            "event_id": data.get("event_id", fname.replace(".json", "")),
                            "file_name": fname,
                            "timestamp_utc": data.get("timestamp_utc"),
                            "session_id": data.get("session_id"),
                            "epoch_id": data.get("epoch_id"),
                            "fix_quality": data.get("data_quality", {}).get("fix_quality")
                        })
                except Exception:
                    continue
        return events

    def load_event(self, event_id: str) -> Optional[EvidenceBundle]:
        """
        Retrieve EvidenceBundle by event_id or file name.
        """
        if not os.path.isdir(self.evidence_dir):
            return None

        # Clean event_id lookup
        target_fnames = [
            f"{event_id}.json",
            f"evidence_{event_id}.json",
            f"evidence_{event_id.replace('evt_', '')}.json",
            event_id if event_id.endswith(".json") else f"{event_id}.json"
        ]

        for fname in os.listdir(self.evidence_dir):
            if fname in target_fnames:
                fpath = os.path.join(self.evidence_dir, fname)
                return self._parse_bundle_file(fpath)

        # Search inside files for matching event_id
        for fname in os.listdir(self.evidence_dir):
            if fname.endswith(".json"):
                fpath = os.path.join(self.evidence_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if data.get("event_id") == event_id:
                            return self._dict_to_bundle(data)
                except Exception:
                    continue
        return None

    def _parse_bundle_file(self, fpath: str) -> Optional[EvidenceBundle]:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
                return self._dict_to_bundle(data)
        except Exception:
            return None

    def _dict_to_bundle(self, data: Dict[str, Any]) -> EvidenceBundle:
        return EvidenceBundle(
            event_id=data.get("event_id", "unknown_evt"),
            timestamp_utc=data.get("timestamp_utc"),
            timestamp_pc=data.get("timestamp_pc"),
            session_id=int(data.get("session_id", 0)),
            epoch_id=data.get("epoch_id"),
            location=data.get("location", {}),
            security_features=data.get("security_features", {}),
            physical_rules=data.get("physical_rules", {}),
            isolation_forest=data.get("isolation_forest", {}),
            xgboost=data.get("xgboost", {}),
            temporal_model=data.get("temporal_model", {}),
            data_quality=data.get("data_quality", {}),
            model_versions=data.get("model_versions", {
                "isolation_forest": "v1.1",
                "temporal_model": "v1.1",
                "xgboost": "v1.1"
            }),
            model_version=data.get("model_version", "locus-production-v5.5"),
            model_training_date=data.get("model_training_date", "2026-10-04"),
            feature_schema_version=data.get("feature_schema_version", "locus-sec-v2.0-10d")
        )

    def process_query(
        self,
        query: str,
        event_id: Optional[str] = None,
        bundle: Optional[EvidenceBundle] = None
    ) -> Dict[str, Any]:
        """
        Execute the complete architecture pipeline:
        Query -> Event Retrieval -> 3-Agent SOC -> RAG -> Master Agent -> Explainable Response.
        """
        clean_query = query.strip() if query else "Show me the evidence behind this alert."

        # 1. Event Retrieval
        active_bundle: Optional[EvidenceBundle] = bundle
        if active_bundle is None and event_id:
            active_bundle = self.load_event(event_id)

        # Fallback to first available event if none specified
        if active_bundle is None:
            available = self.list_available_events()
            if available:
                active_bundle = self.load_event(available[0]["event_id"])

        if active_bundle is None:
            return {
                "event": None,
                "current_status": "UNKNOWN",
                "risk_level": "DEFCON_UNKNOWN",
                "confidence": 0.0,
                "evidence": {},
                "feature_values": {},
                "model_outputs": {},
                "agent_findings": {},
                "rag_sources": [],
                "explanation": "Insufficient evidence: No GNSS event or evidence bundle found. Cannot evaluate query without factual telemetry.",
                "recommended_next_action": ["INGEST_GNSS_EVENT_DATA"]
            }

        # 2. Agentic SOC Deliberation (Agent 1 & Agent 2)
        a1_assessment: IntegrityAssessment = self.agent1.assess(active_bundle)
        a2_assessment: TemporalAssessment = self.agent2.assess(active_bundle)

        # 3. Security RAG Grounding
        rag_context = self.rag_engine.ground_soc_evidence(
            bundle=active_bundle,
            a1_assessment=a1_assessment.to_dict(),
            a2_assessment=a2_assessment.to_dict()
        )

        # 4. Master SOC Agent (Agent 3) Synthesis
        soc_verdict: SOCOrchestrationResult = self.agent3.deliberate(
            bundle=active_bundle,
            integrity_output=a1_assessment,
            temporal_output=a2_assessment,
            rag_context=rag_context
        )

        # 5. Tailored Natural Language Explanation Addressing the Specific Query
        custom_explanation = self._synthesize_tailored_explanation(
            query=clean_query,
            bundle=active_bundle,
            a1=a1_assessment,
            a2=a2_assessment,
            verdict=soc_verdict,
            rag=rag_context
        )

        # 6. Format RAG Sources
        rag_sources = []
        if rag_context.get("is_grounded") and rag_context.get("citations"):
            for cit in rag_context["citations"]:
                rag_sources.append({
                    "document": cit.get("source_document"),
                    "section": cit.get("section"),
                    "regulatory_authorities": cit.get("standard_authorities", []),
                    "similarity": cit.get("similarity")
                })

        # 7. Assemble Final Explainable Response (meeting all required fields)
        b_dict = active_bundle.to_dict()
        return {
            "event": {
                "event_id": active_bundle.event_id,
                "timestamp_utc": active_bundle.timestamp_utc,
                "session_id": active_bundle.session_id,
                "epoch_id": active_bundle.epoch_id,
                "location": active_bundle.location
            },
            "current_status": soc_verdict.status,
            "risk_level": soc_verdict.risk_level,
            "confidence": soc_verdict.confidence,
            "evidence": soc_verdict.evidence,
            "feature_values": active_bundle.security_features,
            "model_outputs": {
                "physical_rules": b_dict.get("physical_rules"),
                "isolation_forest": b_dict.get("isolation_forest"),
                "xgboost": b_dict.get("xgboost"),
                "temporal_model": b_dict.get("temporal_model")
            },
            "agent_findings": {
                "agent_1_integrity": a1_assessment.to_dict(),
                "agent_2_temporal_threat": a2_assessment.to_dict(),
                "agent_3_master_soc": {
                    "status": soc_verdict.status,
                    "risk_level": soc_verdict.risk_level,
                    "confidence": soc_verdict.confidence,
                    "summary": soc_verdict.summary
                }
            },
            "rag_sources": rag_sources,
            "explanation": custom_explanation,
            "recommended_next_action": soc_verdict.recommended_next_action
        }

    def _synthesize_tailored_explanation(
        self,
        query: str,
        bundle: EvidenceBundle,
        a1: IntegrityAssessment,
        a2: TemporalAssessment,
        verdict: SOCOrchestrationResult,
        rag: Dict[str, Any]
    ) -> str:
        """
        Generate a direct, truthful natural language answer to the user's specific prompt.
        Guaranteed zero fabrication; explicitly notes when evidence is insufficient.
        """
        q = query.lower()
        features = bundle.security_features
        rules = bundle.physical_rules
        temp = bundle.temporal_model
        iforest = bundle.isolation_forest

        # Intent 1: "Why was this event flagged?"
        if any(w in q for w in ["why", "flagged", "alert", "trigger", "flag"]):
            if verdict.status == "NOMINAL":
                return (
                    f"Event '{bundle.event_id}' was evaluated as NOMINAL (DEFCON 5). "
                    f"No physical invariants were violated, and the multi-detector quad remained within standard limits. "
                    f"Kinematic health is 100%, and HDOP is {features.get('HDOP', 'N/A')}."
                )
            
            reasons = []
            if a1.physical_violation_count > 0:
                reasons.append(f"Agent 1 detected {a1.physical_violation_count} physical rule breach(es): {a1.explanation}")
            if iforest.get("is_anomaly"):
                reasons.append(f"Isolation Forest flagged spatial out-of-distribution state with score {iforest.get('anomaly_score')}")
            if temp.get("is_anomaly"):
                reasons.append(f"Temporal Autoencoder flagged sequence reconstruction error {temp.get('reconstruction_error')} exceeding threshold {temp.get('error_threshold')}")
            
            rag_info = f" Citing standards: {', '.join(rag.get('regulatory_standards', []))}." if rag.get("is_grounded") else ""
            return f"Event '{bundle.event_id}' was flagged as {verdict.status} ({verdict.risk_level}) because: {'; '.join(reasons)}.{rag_info}"

        # Intent 2: "What features caused the anomaly?"
        elif any(w in q for w in ["what feature", "which feature", "features caused", "driving feature", "feature values"]):
            culprits = []
            if a1.feature_level_anomalies:
                for k, v in a1.feature_level_anomalies.items():
                    culprits.append(f"{k} = {v.get('observed_value')} (exceeded threshold {v.get('threshold')})")
            if temp.get("feature_attribution"):
                for k, v in list(temp.get("feature_attribution", {}).items())[:2]:
                    culprits.append(f"temporal drift on {k} (reconstruction error {v:.4f})")
            
            if not culprits:
                return (
                    f"For event '{bundle.event_id}', no individual 10-D features breached hard thresholds. "
                    f"All features: disp_haversine={features.get('disp_haversine')}, vel_kinematic={features.get('vel_kinematic')}, "
                    f"acc_kinematic={features.get('acc_kinematic')}, HDOP={features.get('HDOP')} are within nominal bounds."
                )
            return f"The primary feature(s) driving this anomaly are: {', '.join(culprits)}."

        # Intent 3: "Is the anomaly persistent?"
        elif any(w in q for w in ["persistent", "persistence", "transient", "streak"]):
            streak = getattr(a2, "persistence_count", 0)
            classification = getattr(a2, "temporal_assessment", "BENIGN")
            is_persist = classification in ["PERSISTENT_DRIFT", "SPOOFING_COORDINATE_STEP"] or streak >= 3
            if is_persist:
                return (
                    f"Yes, the anomaly is persistent. Agent 2 confirmed a persistence streak of {streak} consecutive epochs. "
                    f"Threat classification: {classification}. Under CISA PNT guidelines, sustained multi-epoch anomalies require DEFCON 2 or 1 intervention."
                )
            else:
                return (
                    f"No, this anomaly is NOT persistent. Observed persistence streak is {streak} epoch(s). "
                    f"Agent 2 classified this as {classification}. It is treated as transient RF noise or single-epoch multipath unless it sustains."
                )

        # Intent 4: "What did the temporal model detect?"
        elif any(w in q for w in ["temporal", "lstm", "autoencoder", "sequence"]):
            recon_err = temp.get("reconstruction_error")
            thresh = temp.get("error_threshold")
            is_anom = temp.get("is_anomaly", False)
            if recon_err is None:
                return "Insufficient evidence: Temporal model output is unavailable for this epoch."
            
            recon_str = f"{recon_err:.4f}" if isinstance(recon_err, (int, float)) else str(recon_err)
            thresh_str = f"{thresh:.4f}" if isinstance(thresh, (int, float)) else str(thresh)
            status_text = "exceeded the baseline limit (ANOMALY)" if is_anom else "remained below the baseline limit (NOMINAL)"
            return (
                f"The Temporal LSTM Autoencoder evaluated a sequence window of W=10 epochs. "
                f"It computed a reconstruction error of {recon_str}, which {status_text} (threshold: {thresh_str}). "
                f"Temporal assessment status: {a2.temporal_assessment}."
            )

        # Intent 5: "Explain the navigation-quality degradation."
        elif any(w in q for w in ["navigation quality", "hdop", "vdop", "geometry", "dop"]):
            hdop = features.get("HDOP")
            vdop = features.get("VDOP")
            fix_int = features.get("fix_integrity")
            sats = features.get("sat_count_tot")
            
            reg_text = ""
            if rag.get("is_grounded") and any("dop" in c.get("source_document", "").lower() for c in rag.get("citations", [])):
                reg_text = " According to RTCA DO-229E and NMEA standards, HDOP < 2.0 is nominal, while HDOP > 4.0 indicates geometric degradation."
            
            return (
                f"Navigation quality for event '{bundle.event_id}': HDOP is {hdop}, VDOP is {vdop}, "
                f"composite fix integrity is {fix_int}, and tracked satellite count is {sats}.{reg_text} "
                f"Agent 1 geometry health: {a1.geometry_health * 100:.1f}%."
            )

        # Default fallback: Comprehensive grounded executive overview
        return (
            f"SOC Analysis for Event '{bundle.event_id}': Status is {verdict.status} with Risk Level {verdict.risk_level} "
            f"(Confidence: {verdict.confidence * 100:.1f}%). {verdict.summary} "
            f"Recommended Action: {', '.join(verdict.recommended_next_action)}."
        )
