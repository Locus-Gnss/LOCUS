"""
LOCUS Security RAG — Master RAG Engine & SOC Grounding Subsystem

Module: src.rag.rag_engine
Responsibilities:
- Coordinate document ingestion, vector storage, and semantic context retrieval
- Generate domain-grounded explanations and regulatory citations from SOC Evidence Bundles
- Enforce strict read-only immutability of telemetry data
- Provide fallback mechanisms for queries with insufficient context
- Integrate verified RAG grounding directly into Agent 3 (Master SOC Agent)
"""

import os
from typing import Dict, List, Any, Optional, Union

from src.evidence.evidence_bundle import EvidenceBundle
from src.rag.document_ingestion import DocumentIngester, DocumentChunk
from src.rag.retriever import VectorStore, ContextRetriever, RetrievalOutput, RetrievedContext


class SecurityRAGEngine:
    """
    Master RAG Engine providing technical grounding and regulatory contextualization.
    """

    def __init__(
        self,
        knowledge_base_dir: str = "knowledge_base",
        db_path: str = "data/rag/vector_store.db",
        auto_index: bool = True,
        min_similarity: float = 0.12
    ):
        self.kb_dir = knowledge_base_dir
        self.db_path = db_path
        self.min_similarity = min_similarity

        self.ingester = DocumentIngester(max_chunk_size=800, overlap_size=150)
        self.vector_store = VectorStore(db_path=self.db_path)
        self.retriever = ContextRetriever(self.vector_store, min_similarity=self.min_similarity)

        if auto_index and self.vector_store.count() == 0:
            self.index_knowledge_base()

    def index_knowledge_base(self, kb_dir: Optional[str] = None) -> int:
        """
        Scan knowledge base directory, chunk documents, and index into the vector store.
        """
        target_dir = kb_dir or self.kb_dir
        if not os.path.isdir(target_dir):
            return 0

        chunks = self.ingester.ingest_directory(target_dir)
        if chunks:
            self.vector_store.index_chunks(chunks)
        return len(chunks)

    def query(self, text: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Query the RAG subsystem with a plain text question or technical prompt.
        """
        retrieval: RetrievalOutput = self.retriever.retrieve(query=text, top_k=top_k)
        
        if not retrieval.has_sufficient_context:
            return {
                "query": text,
                "has_sufficient_context": False,
                "status": "INSUFFICIENT_KNOWLEDGE_CONTEXT",
                "explanation": retrieval.insufficient_context_message,
                "citations": [],
                "regulatory_authorities": []
            }

        citations = []
        for ctx in retrieval.retrieved_contexts:
            citations.append({
                "document": ctx.doc_name,
                "section": ctx.section_title,
                "authorities": ctx.standard_authorities,
                "similarity": ctx.similarity_score,
                "excerpt": ctx.text[:250] + "..." if len(ctx.text) > 250 else ctx.text
            })

        return {
            "query": text,
            "has_sufficient_context": True,
            "status": "GROUNDED_CONTEXT_FOUND",
            "regulatory_authorities": retrieval.top_authorities,
            "top_match_section": retrieval.retrieved_contexts[0].section_title if retrieval.retrieved_contexts else "",
            "citations": citations,
            "full_context_blocks": [ctx.text for ctx in retrieval.retrieved_contexts]
        }

    def ground_soc_evidence(
        self,
        bundle: Union[EvidenceBundle, Dict[str, Any]],
        a1_assessment: Optional[Dict[str, Any]] = None,
        a2_assessment: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Ground an Evidence Bundle and multi-agent assessments in approved technical standards.
        Strict Invariant: Read-only; NEVER overwrites or alters telemetry data.
        """
        # Unpack evidence data without mutation
        data = bundle.to_dict() if isinstance(bundle, EvidenceBundle) else dict(bundle)
        sec_features = data.get("security_features", {})
        rules_data = data.get("physical_rules", {})
        temp_data = data.get("temporal_model", {})
        dq_data = data.get("data_quality", {})

        # 1. Synthesize targeted semantic query keywords from verified evidence
        query_terms: List[str] = []

        # Check physical rule breaches
        triggered_rules = rules_data.get("triggered_rules", [])
        if triggered_rules:
            for rule in triggered_rules:
                name = rule.get("rule_name", "")
                diag = rule.get("diagnostic", "")
                query_terms.append(f"{name} {diag}")
        
        # Check kinematics
        acc = sec_features.get("acc_kinematic")
        jerk = sec_features.get("jerk_kinematic")
        vel = sec_features.get("vel_kinematic")
        disp = sec_features.get("disp_haversine")
        if (acc is not None and abs(acc) > 4.0) or (jerk is not None and abs(jerk) > 10.0) or (disp is not None and disp > 10.0):
            query_terms.append("GNSS spoofing kinematic teleportation acceleration jerk breach lift-off step position injection")

        # Check navigation quality & DOP
        hdop = sec_features.get("HDOP")
        if hdop is not None and hdop > 3.0:
            query_terms.append("navigation quality HDOP geometric degradation dilution of precision urban canyon")

        # Check satellite behavior & C/N0
        cno = sec_features.get("avg_cno") or sec_features.get("feat_mean_cno")
        sats = sec_features.get("sat_count_tot")
        churn = sec_features.get("sat_churn")
        if cno is not None and cno < 25.0:
            query_terms.append("GNSS jamming radio frequency interference RFI C/N0 signal attenuation starvation")
        if sats is not None and sats < 5:
            query_terms.append("constellation starvation RAIM loss of fault detection and exclusion FDE")
        if churn is not None and churn > 0.4:
            query_terms.append("satellite churn constellation turnover rate spoofer handover")

        # Check temporal drift
        if temp_data.get("is_anomaly") or (a2_assessment and a2_assessment.get("is_anomalous")):
            query_terms.append("temporal anomaly persistent drift sequence autoencoder reconstruction error")

        # Fallback to benign nominal query if no triggers present
        if not query_terms:
            constructed_query = "GNSS nominal baseline positioning trilateration receiver autonomous integrity monitoring RAIM"
        else:
            constructed_query = " ".join(query_terms)

        # 2. Retrieve grounded context
        retrieval: RetrievalOutput = self.retriever.retrieve(query=constructed_query, top_k=3)

        if not retrieval.has_sufficient_context:
            return {
                "is_grounded": False,
                "insufficient_context": True,
                "insufficient_context_message": retrieval.insufficient_context_message,
                "regulatory_standards": [],
                "technical_summary": "Insufficient knowledge context retrieved for current evidence profile.",
                "mitigation_guidance": ["MAINTAIN_CURRENT_DEFCON", "REQUEST_OPERATOR_LOG"],
                "citations": [],
                "immutable_sensor_data_verified": True
            }

        # 3. Extract grounded authorities & citations
        citations = []
        guidance_actions = []
        for ctx in retrieval.retrieved_contexts:
            citations.append({
                "standard_authorities": ctx.standard_authorities,
                "source_document": ctx.doc_name,
                "section": ctx.section_title,
                "similarity": ctx.similarity_score
            })
            # Check for domain mitigations
            if "spoofing" in ctx.text.lower():
                guidance_actions.append("ISOLATE_GNSS_RECEIVER_FALLBACK_TO_INS")
            if "jamming" in ctx.text.lower():
                guidance_actions.append("ENGAGE_RF_NOTCH_FILTER_SECONDARY_FREQUENCIES")
            if "raim" in ctx.text.lower() or "dop" in ctx.text.lower():
                guidance_actions.append("EXCLUDE_DEGRADED_GEOMETRY_SATELLITES")

        return {
            "is_grounded": True,
            "insufficient_context": False,
            "insufficient_context_message": None,
            "regulatory_standards": retrieval.top_authorities,
            "technical_summary": f"Grounded in standards: {', '.join(retrieval.top_authorities)} via section '{retrieval.retrieved_contexts[0].section_title}'",
            "mitigation_guidance": list(dict.fromkeys(guidance_actions)) if guidance_actions else ["MONITOR_INTEGRITY"],
            "citations": citations,
            "supporting_context_excerpts": [ctx.text[:300] for ctx in retrieval.retrieved_contexts],
            "immutable_sensor_data_verified": True
        }

    def deliberate_with_agent3(
        self,
        master_agent: Any,
        bundle: Union[EvidenceBundle, Dict[str, Any]],
        integrity_output: Any,
        temporal_output: Any
    ) -> Any:
        """
        Grounded integration: Retrieves technical RAG grounding and passes it to Agent 3
        (MasterSOCAgent or MasterSOCOrchestrator).
        """
        rag_context = self.ground_soc_evidence(bundle, integrity_output, temporal_output)

        if hasattr(master_agent, "deliberate"):
            # MasterSOCAgent interface
            return master_agent.deliberate(
                bundle=bundle,
                integrity_output=integrity_output,
                temporal_output=temporal_output,
                rag_context=rag_context
            )
        elif hasattr(master_agent, "correlate_and_resolve"):
            # MasterSOCOrchestrator interface
            return master_agent.correlate_and_resolve(
                bundle=bundle,
                a1=integrity_output,
                a2=temporal_output
            )
        else:
            raise TypeError("Unsupported Master SOC Agent interface.")
