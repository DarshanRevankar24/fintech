from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ChunkMetadata(BaseModel):
    chunk_id: str
    file_name: str
    file_path: str
    company: str
    fy: str
    quarter: str
    date: str
    title: Optional[str] = None
    section: Optional[str] = None
    start_word_idx: int
    end_word_idx: int

class ChunkRecord(BaseModel):
    text: str
    metadata: ChunkMetadata

class SearchQuery(BaseModel):
    query: str
    top_k: int = 5
    filters: Optional[Dict[str, Any]] = None

class SearchResult(BaseModel):
    score: float
    text: str
    metadata: ChunkMetadata

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
