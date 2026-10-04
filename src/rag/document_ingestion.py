"""
LOCUS Security RAG — Document Ingestion & Chunking Pipeline

Module: src.rag.document_ingestion
Responsibilities:
- Ingest approved technical documents from knowledge_base/
- Extract domain metadata, standard authorities (ICAO, RTCA, CISA, MITRE), and tags
- Semantic chunking respecting markdown section headers with configurable size and overlap
- Produce structured DocumentChunk objects for vector indexing
"""

import os
import re
import uuid
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional


@dataclass
class DocumentChunk:
    """
    Structured document chunk with technical provenance metadata.
    """
    chunk_id: str
    doc_name: str
    title: str
    section_title: str
    text: str
    standard_authorities: List[str]
    tags: List[str]
    chunk_index: int
    char_count: int = 0

    def __post_init__(self):
        if not self.char_count:
            self.char_count = len(self.text)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DocumentIngester:
    """
    Ingests and parses technical reference documents for the Security RAG knowledge base.
    """

    def __init__(self, max_chunk_size: int = 800, overlap_size: int = 150):
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size

    def ingest_directory(self, dir_path: str) -> List[DocumentChunk]:
        """
        Scan and ingest all supported files (.md, .txt) in the directory.
        """
        if not os.path.isdir(dir_path):
            raise FileNotFoundError(f"Knowledge base directory not found: {dir_path}")

        chunks: List[DocumentChunk] = []
        for root, _, files in os.walk(dir_path):
            for file in sorted(files):
                if file.endswith((".md", ".txt")):
                    file_path = os.path.join(root, file)
                    file_chunks = self.ingest_file(file_path)
                    chunks.extend(file_chunks)

        return chunks

    def ingest_file(self, file_path: str) -> List[DocumentChunk]:
        """
        Ingest a single document and split into semantic chunks.
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        doc_name = os.path.basename(file_path)
        doc_metadata = self._extract_metadata(content, doc_name)

        return self._chunk_document(content, doc_name, doc_metadata)

    def _extract_metadata(self, content: str, default_name: str) -> Dict[str, Any]:
        """
        Extract document title, standard authorities, and domain tags.
        """
        meta = {
            "title": default_name,
            "authorities": [],
            "tags": []
        }

        # Extract title from first markdown header
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if title_match:
            meta["title"] = title_match.group(1).strip()

        # Extract Standard Authorities
        auth_match = re.search(r"\*\*Standard Authorities\*\*:\s*([^\n]+)", content, re.IGNORECASE)
        if auth_match:
            raw_auth = auth_match.group(1).strip()
            meta["authorities"] = [a.strip() for a in raw_auth.split(",") if a.strip()]

        # Extract Domain Tags
        tags_match = re.search(r"\*\*Domain Tags\*\*:\s*([^\n]+)", content, re.IGNORECASE)
        if tags_match:
            raw_tags = tags_match.group(1).strip()
            # Extract tags inside backticks or comma-separated
            extracted_tags = re.findall(r"`([^`]+)`", raw_tags)
            if not extracted_tags:
                extracted_tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
            meta["tags"] = extracted_tags

        return meta

    def _chunk_document(self, content: str, doc_name: str, meta: Dict[str, Any]) -> List[DocumentChunk]:
        """
        Segment markdown content into section-aware chunks.
        """
        chunks: List[DocumentChunk] = []
        
        # Split by level 2 or 3 markdown headers (## Section)
        section_pattern = re.compile(r"(^#{2,3}\s+.+$)", re.MULTILINE)
        sections = section_pattern.split(content)

        current_section_title = "Overview"
        chunk_idx = 0

        for part in sections:
            part = part.strip()
            if not part:
                continue

            # Check if this part is a header
            if section_pattern.match(part):
                current_section_title = re.sub(r"^#{2,3}\s+", "", part).strip()
                continue

            # This is section body text; split if too large
            if len(part) <= self.max_chunk_size:
                chunk_text = f"[{meta['title']} - {current_section_title}]\n{part}"
                chunks.append(DocumentChunk(
                    chunk_id=f"{doc_name}_{chunk_idx}",
                    doc_name=doc_name,
                    title=meta["title"],
                    section_title=current_section_title,
                    text=chunk_text,
                    standard_authorities=meta["authorities"],
                    tags=meta["tags"],
                    chunk_index=chunk_idx
                ))
                chunk_idx += 1
            else:
                # Sub-chunk with overlap
                start = 0
                while start < len(part):
                    end = min(start + self.max_chunk_size, len(part))
                    sub_text = part[start:end].strip()
                    if sub_text:
                        chunk_text = f"[{meta['title']} - {current_section_title} (part)]\n{sub_text}"
                        chunks.append(DocumentChunk(
                            chunk_id=f"{doc_name}_{chunk_idx}",
                            doc_name=doc_name,
                            title=meta["title"],
                            section_title=current_section_title,
                            text=chunk_text,
                            standard_authorities=meta["authorities"],
                            tags=meta["tags"],
                            chunk_index=chunk_idx
                        ))
                        chunk_idx += 1
                    if end >= len(part):
                        break
                    start += (self.max_chunk_size - self.overlap_size)

        return chunks
