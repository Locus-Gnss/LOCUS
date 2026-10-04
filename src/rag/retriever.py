"""
LOCUS Security RAG — Vector Database & Context Retriever

Module: src.rag.retriever
Responsibilities:
- Create vector embeddings from text chunks
- Store chunks and vector embeddings in a persistent local SQLite database
- Semantic similarity search (cosine distance) for evidence queries
- Enforce strict metadata preservation (authorities, document, tags)
- Explicit insufficient context handling to prevent unsupported claims
"""

import os
import json
import sqlite3
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib

from src.rag.document_ingestion import DocumentChunk


@dataclass
class RetrievedContext:
    """
    Retrieved knowledge chunk with explicit source and authority metadata.
    """
    chunk_id: str
    doc_name: str
    title: str
    section_title: str
    text: str
    standard_authorities: List[str]
    tags: List[str]
    similarity_score: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RetrievalOutput:
    """
    Standardized retrieval response with grounding and sufficiency guarantees.
    """
    query: str
    retrieved_contexts: List[RetrievedContext]
    has_sufficient_context: bool
    insufficient_context_message: Optional[str] = None
    top_authorities: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class VectorStore:
    """
    Local SQLite-backed vector store for RAG document embeddings.
    """

    def __init__(self, db_path: str = "data/rag/vector_store.db", vectorizer_path: Optional[str] = None):
        self.db_path = db_path
        if self.db_path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self.vectorizer_path = vectorizer_path or (
            os.path.join(os.path.dirname(os.path.abspath(self.db_path)), "vectorizer.joblib")
            if self.db_path != ":memory:" else None
        )
        self.vectorizer: Optional[TfidfVectorizer] = None
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id TEXT PRIMARY KEY,
                    doc_name TEXT,
                    title TEXT,
                    section_title TEXT,
                    text TEXT,
                    authorities_json TEXT,
                    tags_json TEXT,
                    chunk_index INTEGER,
                    embedding_blob BLOB
                )
            """)
            conn.commit()

        # Load existing vectorizer if available
        if self.vectorizer_path and os.path.exists(self.vectorizer_path):
            try:
                self.vectorizer = joblib.load(self.vectorizer_path)
            except Exception:
                self.vectorizer = None

    def index_chunks(self, chunks: List[DocumentChunk]):
        """
        Embed and persist document chunks into the SQLite vector store.
        """
        if not chunks:
            return

        texts = [chunk.text for chunk in chunks]
        
        # Fit vectorizer on full corpus with word and character n-grams for robust retrieval
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            sublinear_tf=True,
            max_features=5000,
            token_pattern=r"(?u)\b\w+\b"
        )
        embeddings = self.vectorizer.fit_transform(texts).toarray().astype(np.float32)

        # Normalize L2
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        embeddings = embeddings / norms

        if self.vectorizer_path:
            joblib.dump(self.vectorizer, self.vectorizer_path)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for chunk, emb in zip(chunks, embeddings):
                cursor.execute("""
                    INSERT OR REPLACE INTO chunks 
                    (chunk_id, doc_name, title, section_title, text, authorities_json, tags_json, chunk_index, embedding_blob)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    chunk.chunk_id,
                    chunk.doc_name,
                    chunk.title,
                    chunk.section_title,
                    chunk.text,
                    json.dumps(chunk.standard_authorities),
                    json.dumps(chunk.tags),
                    chunk.chunk_index,
                    emb.tobytes()
                ))
            conn.commit()

    def count(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM chunks")
            return cursor.fetchone()[0]

    def search(self, query: str, top_k: int = 3, min_similarity: float = 0.12) -> List[RetrievedContext]:
        """
        Cosine similarity search over stored chunk embeddings.
        """
        if self.vectorizer is None or self.count() == 0:
            return []

        # Embed query
        q_emb = self.vectorizer.transform([query]).toarray().astype(np.float32)
        q_norm = np.linalg.norm(q_emb)
        if q_norm > 0:
            q_emb = q_emb / q_norm
        else:
            return []

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT chunk_id, doc_name, title, section_title, text, authorities_json, tags_json, embedding_blob 
                FROM chunks
            """)
            rows = cursor.fetchall()

        if not rows:
            return []

        results: List[Tuple[float, RetrievedContext]] = []
        for row in rows:
            chunk_id, doc_name, title, section_title, text, auth_json, tags_json, emb_blob = row
            c_emb = np.frombuffer(emb_blob, dtype=np.float32)
            
            # Cosine similarity
            sim = float(np.dot(q_emb[0], c_emb))
            if sim >= min_similarity:
                results.append((sim, RetrievedContext(
                    chunk_id=chunk_id,
                    doc_name=doc_name,
                    title=title,
                    section_title=section_title,
                    text=text,
                    standard_authorities=json.loads(auth_json),
                    tags=json.loads(tags_json),
                    similarity_score=round(sim, 4)
                )))

        # Sort descending by similarity
        results.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in results[:top_k]]


class ContextRetriever:
    """
    Retriever engine that wraps VectorStore with strict validation and fallback logic.
    """

    def __init__(self, vector_store: VectorStore, min_similarity: float = 0.12):
        self.vector_store = vector_store
        self.min_similarity = min_similarity

    def retrieve(self, query: str, top_k: int = 3) -> RetrievalOutput:
        """
        Retrieve context with explicit insufficient context indication if no relevant sources found.
        """
        if not query or not query.strip():
            return RetrievalOutput(
                query=query,
                retrieved_contexts=[],
                has_sufficient_context=False,
                insufficient_context_message="Empty query provided; insufficient knowledge context.",
                top_authorities=[]
            )

        contexts = self.vector_store.search(query=query, top_k=top_k, min_similarity=self.min_similarity)

        if not contexts:
            return RetrievalOutput(
                query=query,
                retrieved_contexts=[],
                has_sufficient_context=False,
                insufficient_context_message=f"Insufficient knowledge context retrieved for query: '{query}'. No supported regulatory citations found.",
                top_authorities=[]
            )

        # Aggregate unique authorities
        authorities = []
        for ctx in contexts:
            for auth in ctx.standard_authorities:
                if auth not in authorities:
                    authorities.append(auth)

        return RetrievalOutput(
            query=query,
            retrieved_contexts=contexts,
            has_sufficient_context=True,
            insufficient_context_message=None,
            top_authorities=authorities
        )
