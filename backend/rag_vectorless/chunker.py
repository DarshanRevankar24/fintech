import re
from typing import List, Dict, Any
from .schemas import ChunkRecord, ChunkMetadata
import hashlib

# Typical transcript sections
SECTION_MARKERS = [
    "Prepared Remarks",
    "Question-and-Answer",
    "Q&A",
    "Question-and-Answer Session",
    "Operator"
]

def find_sections(text: str) -> List[Dict[str, Any]]:
    """Simple heuristic to find sections based on common headers."""
    sections = []
    current_section = "General"
    current_start = 0
    
    lines = text.split('\n')
    
    word_count = 0
    for line in lines:
        line_clean = line.strip()
        for marker in SECTION_MARKERS:
            # Case insensitive exact or close match
            if line_clean.lower() == marker.lower() or (len(line_clean) < 50 and marker.lower() in line_clean.lower()):
                if word_count > current_start:
                    sections.append({
                        "name": current_section,
                        "start_word": current_start,
                        "end_word": word_count
                    })
                current_section = marker
                current_start = word_count
                break
        
        words_in_line = len(re.findall(r'\S+', line))
        word_count += words_in_line
        
    sections.append({
        "name": current_section,
        "start_word": current_start,
        "end_word": word_count
    })
    
    return sections

def get_section_for_word(word_idx: int, sections: List[Dict[str, Any]]) -> str:
    for sec in sections:
        if sec["start_word"] <= word_idx <= sec["end_word"]:
            return sec["name"]
        if sec == sections[-1] and word_idx >= sec["end_word"]:
            return sec["name"]
    return "Unknown"

def chunk_text(doc: Dict[str, Any], chunk_size: int = 400, overlap: int = 80) -> List[ChunkRecord]:
    text = doc["text"]
    meta = doc["metadata"]
    filename = doc["file_name"]
    filepath = doc["file_path"]
    
    sections = find_sections(text)
    
    words = re.findall(r'\S+', text)
    
    chunks = []
    start_idx = 0
    
    while start_idx < len(words):
        end_idx = min(start_idx + chunk_size, len(words))
        
        chunk_words = words[start_idx:end_idx]
        chunk_text_str = " ".join(chunk_words)
        
        mid_idx = start_idx + (len(chunk_words) // 2)
        section = get_section_for_word(mid_idx, sections)
        
        if "q&a" in section.lower() or "question-and-answer" in section.lower():
            section = "q&a"
            
        chunk_id = hashlib.md5(f"{filename}_{start_idx}_{end_idx}".encode()).hexdigest()[:12]
        
        chunk_meta = ChunkMetadata(
            chunk_id=chunk_id,
            file_name=filename,
            file_path=filepath,
            company=meta.get("company", "unknown"),
            fy=meta.get("fy", "unknown"),
            quarter=meta.get("quarter", "unknown"),
            date=meta.get("date", "unknown"),
            title=meta.get("title"),
            section=section,
            start_word_idx=start_idx,
            end_word_idx=end_idx
        )
        
        chunks.append(ChunkRecord(text=chunk_text_str, metadata=chunk_meta))
        
        if end_idx == len(words):
            break
            
        start_idx += (chunk_size - overlap)
        
    return chunks
