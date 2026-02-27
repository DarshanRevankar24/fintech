import os
import json
import pickle
from typing import List, Dict, Any, Tuple
from rank_bm25 import BM25Okapi
import re
from .schemas import ChunkRecord
from .loader import load_manifest, load_transcripts, MANIFEST_FILE
from .chunker import chunk_text

CACHE_DIR = "./index_cache"
CHUNKS_FILE = os.path.join(CACHE_DIR, "chunks.jsonl")
BM25_FILE = os.path.join(CACHE_DIR, "bm25.pkl")
MANIFEST_SNAPSHOT = os.path.join(CACHE_DIR, "manifest_snapshot.json")
FILE_STATE = os.path.join(CACHE_DIR, "file_state.json")

# Simple stopword list
STOPWORDS = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "by", "as", "is", "are", "was", "were", "it", "this", "that"}

def tokenize(text: str) -> List[str]:
    text = text.lower()
    # Keep alphanumerics
    words = re.findall(r'[a-z0-9]+', text)
    return [w for w in words if w not in STOPWORDS]

def get_file_states(transcripts_dir: str) -> Dict[str, float]:
    states = {}
    if not os.path.exists(transcripts_dir):
        return states
    for f in os.listdir(transcripts_dir):
        if f.endswith(".txt") or f == MANIFEST_FILE:
            fpath = os.path.join(transcripts_dir, f)
            states[f] = os.path.getmtime(fpath)
    return states

def needs_rebuild(transcripts_dir: str) -> bool:
    if not os.path.exists(CACHE_DIR):
        return True
    if not os.path.exists(CHUNKS_FILE) or not os.path.exists(BM25_FILE):
        return True
        
    # Check if files changed
    if os.path.exists(FILE_STATE):
        with open(FILE_STATE, "r") as f:
            old_states = json.load(f)
        current_states = get_file_states(transcripts_dir)
        if old_states != current_states:
            return True
            
    return False

class BM25Index:
    def __init__(self):
        self.bm25: BM25Okapi = None
        self.chunks: List[ChunkRecord] = []
        
    def build(self, transcripts_dir: str):
        print("Building BM25 Index...")
        docs = load_transcripts(transcripts_dir)
        
        self.chunks = []
        for doc in docs:
            doc_chunks = chunk_text(doc)
            self.chunks.extend(doc_chunks)
            
        # Tokenize corpus
        corpus_tokens = [tokenize(chunk.text) for chunk in self.chunks]
        self.bm25 = BM25Okapi(corpus_tokens)
        
        self.save(transcripts_dir)
        print(f"Index built with {len(self.chunks)} chunks.")
        
    def save(self, transcripts_dir: str):
        os.makedirs(CACHE_DIR, exist_ok=True)
        
        with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
            for c in self.chunks:
                f.write(c.json() + "\n")
                
        with open(BM25_FILE, "wb") as f:
            pickle.dump(self.bm25, f)
            
        with open(FILE_STATE, "w") as f:
            json.dump(get_file_states(transcripts_dir), f)
            
        manifest = load_manifest(transcripts_dir)
        with open(MANIFEST_SNAPSHOT, "w", encoding="utf-8") as f:
            json.dump(manifest, f)
            
    def load(self):
        print("Loading BM25 Index from cache...")
        self.chunks = []
        with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                self.chunks.append(ChunkRecord.parse_raw(line))
                
        with open(BM25_FILE, "rb") as f:
            self.bm25 = pickle.load(f)
        print("Index loaded.")

global_index = BM25Index()

def build_index_if_needed(transcripts_dir: str = "./transcripts"):
    if needs_rebuild(transcripts_dir):
        global_index.build(transcripts_dir)
    else:
        global_index.load()

def get_index() -> BM25Index:
    return global_index
