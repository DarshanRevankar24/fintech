import os
import json
from typing import List, Dict, Any

MANIFEST_FILE = "manifest.json"

def infer_company_from_filename(filename: str) -> str:
    lower_name = filename.lower()
    if "nvidia" in lower_name or "nvda" in lower_name:
        return "NVDA"
    if "apple" in lower_name or "aapl" in lower_name:
        return "AAPL"
    if "microsoft" in lower_name or "msft" in lower_name:
        return "MSFT"
    return "UNKNOWN"

def load_manifest(transcripts_dir: str) -> Dict[str, Any]:
    manifest_path = os.path.join(transcripts_dir, MANIFEST_FILE)
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def generate_manifest_template(transcripts_dir: str) -> Dict[str, Any]:
    template = {}
    if not os.path.exists(transcripts_dir):
        return template
        
    for filename in os.listdir(transcripts_dir):
        if filename.endswith(".txt"):
            company = infer_company_from_filename(filename)
            template[filename] = {
                "company": company,
                "fy": "unknown",
                "quarter": "unknown",
                "date": "unknown",
                "title": f"Earnings Call: {filename}"
            }
    return template

def load_transcripts(transcripts_dir: str) -> List[Dict[str, Any]]:
    """Loads all transcripts and merges manifest metadata."""
    if not os.path.exists(transcripts_dir):
        os.makedirs(transcripts_dir)
        
    manifest = load_manifest(transcripts_dir)
    documents = []
    
    for filename in os.listdir(transcripts_dir):
        if not filename.endswith(".txt"):
            continue
            
        file_path = os.path.join(transcripts_dir, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
            
        meta = manifest.get(filename, {})
        
        # Fallbacks for missing manifest data
        if not meta:
            meta["company"] = infer_company_from_filename(filename)
            meta["fy"] = "unknown"
            meta["quarter"] = "unknown"
            meta["date"] = "unknown"
            
        documents.append({
            "text": text,
            "file_name": filename,
            "file_path": file_path,
            "metadata": meta
        })
        
    return documents
