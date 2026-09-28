"""
LOCUS Phase 6 — 3-Agent Security SOC Pipeline Runner

Module: src.soc.soc_pipeline
Orchestrates stream and batch ingestion of Evidence Bundles through the
3-agent hierarchy:
1. Agent 1: GNSS Integrity Agent (Physical Invariants & Geometry)
2. Agent 2: Temporal Threat Correlation Agent (Dynamics & Convergence)
3. Agent 3: Master SOC Orchestrator (Consensus, DEFCON & Mitigations)
"""

import os
import json
import glob
from typing import Dict, List, Optional, Union, Any, Generator, Tuple
import pandas as pd

from src.evidence.evidence_bundle import EvidenceBundle
from src.soc.models import (
    Agent1Assessment,
    Agent2Assessment,
    SOCIncidentReport,
    DefconLevel
)
from src.soc.integrity_agent import GNSSIntegrityAgent
from src.soc.temporal_threat_agent import TemporalThreatAgent
from src.soc.master_soc_orchestrator import MasterSOCOrchestrator

DEFAULT_INCIDENTS_DIR = os.path.join("data", "incidents")


class SOCPipeline:
    """
    End-to-End SOC orchestration pipeline connecting Evidence Bundles
    to the 3-Agent hierarchy and producing auditable incident reports.
    """

    def __init__(
        self,
        integrity_agent: Optional[GNSSIntegrityAgent] = None,
        threat_agent: Optional[TemporalThreatAgent] = None,
        orchestrator: Optional[MasterSOCOrchestrator] = None,
        incidents_dir: str = DEFAULT_INCIDENTS_DIR
    ):
        self.integrity_agent = integrity_agent or GNSSIntegrityAgent()
        self.threat_agent = threat_agent or TemporalThreatAgent()
        self.orchestrator = orchestrator or MasterSOCOrchestrator()
        self.incidents_dir = incidents_dir
        os.makedirs(self.incidents_dir, exist_ok=True)

    def process_epoch(
        self,
        bundle: Union[EvidenceBundle, Dict[str, Any]]
    ) -> Tuple[Agent1Assessment, Agent2Assessment, SOCIncidentReport]:
        """
        Process a single epoch bundle through the 3-agent chain.
        """
        a1 = self.integrity_agent.assess(bundle)
        a2 = self.threat_agent.assess(bundle)
        incident = self.orchestrator.correlate_and_resolve(bundle, a1, a2)
        return a1, a2, incident

    def process_bundle_stream(
        self,
        bundles: List[Union[EvidenceBundle, Dict[str, Any]]],
        save_incidents: bool = True,
        incident_defcon_threshold: DefconLevel = DefconLevel.DEFCON_4
    ) -> Tuple[List[SOCIncidentReport], Dict[str, Any]]:
        """
        Stream a sequence of bundles through the SOC pipeline.
        Saves incidents that meet or exceed the DEFCON threshold (e.g. DEFCON 1..4).
        """
        incidents: List[SOCIncidentReport] = []
        defcon_counts: Dict[str, int] = {lvl.value: 0 for lvl in DefconLevel}
        vector_counts: Dict[str, int] = {}
        consensus_counts: Dict[str, int] = {}
        mitigation_counts: Dict[str, int] = {}

        severity_rank = {
            DefconLevel.DEFCON_5: 5,
            DefconLevel.DEFCON_4: 4,
            DefconLevel.DEFCON_3: 3,
            DefconLevel.DEFCON_2: 2,
            DefconLevel.DEFCON_1: 1,
        }
        thresh_rank = severity_rank[incident_defcon_threshold]

        saved_files = 0
        jsonl_path = os.path.join(self.incidents_dir, "soc_incidents_stream.jsonl")
        jsonl_file = open(jsonl_path, "w", encoding="utf-8") if save_incidents else None

        try:
            for idx, b in enumerate(bundles):
                a1, a2, inc = self.process_epoch(b)
                incidents.append(inc)

                # Metrics accounting
                defcon_counts[inc.defcon_level.value] = defcon_counts.get(inc.defcon_level.value, 0) + 1
                vector_counts[inc.attack_vector] = vector_counts.get(inc.attack_vector, 0) + 1
                consensus_counts[inc.consensus_status] = consensus_counts.get(inc.consensus_status, 0) + 1

                for m in inc.mitigation_actions:
                    mitigation_counts[m] = mitigation_counts.get(m, 0) + 1

                if save_incidents and jsonl_file is not None:
                    jsonl_file.write(inc.to_json(indent=None) + "\n")

                # If incident is notable (DEFCON <= threshold), save individual JSON
                if save_incidents and severity_rank[inc.defcon_level] <= thresh_rank:
                    fname = f"incident_{inc.session_id}_{inc.epoch_id or idx}_{inc.defcon_level.value.lower()}.json"
                    fpath = os.path.join(self.incidents_dir, fname)
                    with open(fpath, "w", encoding="utf-8") as f:
                        f.write(inc.to_json(indent=2))
                    saved_files += 1

        finally:
            if jsonl_file is not None:
                jsonl_file.close()

        summary = {
            "total_epochs_processed": len(bundles),
            "defcon_distribution": defcon_counts,
            "attack_vectors": vector_counts,
            "consensus_distribution": consensus_counts,
            "mitigations_issued": mitigation_counts,
            "notable_incidents_saved": saved_files,
            "stream_log": jsonl_path if save_incidents else None
        }

        # Persist summary
        if save_incidents:
            summary_path = os.path.join(self.incidents_dir, "soc_run_summary.json")
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)

        return incidents, summary

    def process_evidence_jsonl(
        self,
        jsonl_path: str = "data/evidence/evidence_stream_sample.jsonl",
        max_epochs: Optional[int] = None
    ) -> Tuple[List[SOCIncidentReport], Dict[str, Any]]:
        """
        Process an evidence JSONL stream file directly.
        """
        if not os.path.exists(jsonl_path):
            raise FileNotFoundError(f"Evidence stream file not found: {jsonl_path}")

        bundles: List[Dict[str, Any]] = []
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if max_epochs is not None and i >= max_epochs:
                    break
                stripped = line.strip()
                if stripped:
                    bundles.append(json.loads(stripped))

        print(f"Loaded {len(bundles)} evidence bundles from {jsonl_path}")
        return self.process_bundle_stream(bundles)

    def process_evidence_directory(
        self,
        evidence_dir: str = "data/evidence",
        max_files: Optional[int] = None
    ) -> Tuple[List[SOCIncidentReport], Dict[str, Any]]:
        """
        Process individual evidence JSON files from a directory.
        """
        pattern = os.path.join(evidence_dir, "evidence_*_*.json")
        file_list = sorted(glob.glob(pattern))
        if max_files:
            file_list = file_list[:max_files]

        bundles: List[Dict[str, Any]] = []
        for fp in file_list:
            with open(fp, "r", encoding="utf-8") as f:
                bundles.append(json.load(f))

        print(f"Loaded {len(bundles)} evidence bundle files from {evidence_dir}")
        return self.process_bundle_stream(bundles)


def run_phase_6_pipeline():
    """
    Standalone runner for Phase 6 3-Agent Security SOC.
    Processes available evidence stream and outputs incident artifacts.
    """
    print("=" * 70)
    print("LOCUS PHASE 6: 3-AGENT AGENTIC SECURITY SOC PIPELINE")
    print("=" * 70)

    evidence_jsonl = os.path.join("data", "evidence", "evidence_stream_sample.jsonl")
    pipeline = SOCPipeline()

    if os.path.exists(evidence_jsonl):
        print(f"Executing SOC analysis on evidence stream: {evidence_jsonl}")
        incidents, summary = pipeline.process_evidence_jsonl(evidence_jsonl)
    else:
        print("Stream sample not found; executing on evidence directory...")
        incidents, summary = pipeline.process_evidence_directory()

    print("\n--- Phase 6 SOC Summary ---")
    print(f"Total Epochs Processed: {summary['total_epochs_processed']}")
    print(f"DEFCON Distribution:    {summary['defcon_distribution']}")
    print(f"Attack Vectors:         {summary['attack_vectors']}")
    print(f"Consensus Breakdown:    {summary['consensus_distribution']}")
    print(f"Notable Incidents Saved: {summary['notable_incidents_saved']}")
    print("=" * 70)
    return incidents, summary


if __name__ == "__main__":
    run_phase_6_pipeline()
