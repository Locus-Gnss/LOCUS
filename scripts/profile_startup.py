import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def measure(label, fn):
    t0 = time.perf_counter()
    res = fn()
    dur = time.perf_counter() - t0
    print(f"{label:<40}: {dur:.4f}s", flush=True)
    return res, dur

print("=== DETAILED IN-PROCESS STARTUP BREAKDOWN ===", flush=True)
_, t_np = measure("import numpy", lambda: __import__('numpy'))
_, t_pd = measure("import pandas", lambda: __import__('pandas'))
_, t_sp = measure("import scipy", lambda: __import__('scipy'))
_, t_sk = measure("import sklearn", lambda: __import__('sklearn'))
_, t_fa = measure("import fastapi", lambda: __import__('fastapi'))
_, t_th = measure("import torch", lambda: __import__('torch'))
_, t_xgb = measure("import xgboost", lambda: __import__('xgboost'))

print("\n--- LOCUS Internal Modules ---", flush=True)
_, t_bundle = measure("import src.evidence.evidence_bundle", lambda: __import__('src.evidence.evidence_bundle'))
_, t_rag = measure("import src.rag.rag_engine", lambda: __import__('src.rag.rag_engine'))
_, t_ag1 = measure("import src.agents.integrity_agent", lambda: __import__('src.agents.integrity_agent'))
_, t_ag2 = measure("import src.agents.temporal_threat_agent", lambda: __import__('src.agents.temporal_threat_agent'))
_, t_ag3 = measure("import src.agents.master_soc_agent", lambda: __import__('src.agents.master_soc_agent'))
_, t_qp = measure("import src.query.query_processor", lambda: __import__('src.query.query_processor'))

print("\n--- Instantiation Overhead ---", flush=True)
from src.query.query_processor import SecurityQueryProcessor
qp, t_qp_init = measure("SecurityQueryProcessor() init", lambda: SecurityQueryProcessor())
_, t_events = measure("qp.list_available_events()", lambda: qp.list_available_events())
_, t_rag_count = measure("qp.rag_engine.vector_store.count()", lambda: qp.rag_engine.vector_store.count())

print("\n--- Complete App Import ---", flush=True)
_, t_app = measure("import src.api.app", lambda: __import__('src.api.app'))
