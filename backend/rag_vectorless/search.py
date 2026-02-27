from typing import List, Dict, Any, Tuple
from .schemas import SearchQuery, SearchResult
from .indexer import get_index, tokenize

def search_index(query_req: SearchQuery) -> List[SearchResult]:
    index = get_index()
    if not index.bm25 or not index.chunks:
        return []
        
    query_text = query_req.query
    filters = query_req.filters or {}
    top_k = query_req.top_k
    
    tokenized_query = tokenize(query_text)
    
    # Get initial BM25 scores
    scores = index.bm25.get_scores(tokenized_query)
    
    results = []
    
    # Check boost terms
    has_guidance = "guidance" in query_text.lower() or "outlook" in query_text.lower()
    has_azure = "azure" in query_text.lower()
    has_question = "?" in query_text
    
    for i, (score, chunk) in enumerate(zip(scores, index.chunks)):
        if score <= 0:
            continue
            
        # Apply filters
        pass_filter = True
        if filters:
            for k, v in filters.items():
                chunk_val = getattr(chunk.metadata, k, None)
                if chunk_val != v:
                    pass_filter = False
                    break
                    
        if not pass_filter:
            continue
            
        # Apply boosts
        boosted_score = score
        chunk_text_lower = chunk.text.lower()
        
        if has_guidance and ("guidance" in chunk_text_lower or "outlook" in chunk_text_lower):
            boosted_score *= 1.10
            
        if has_azure and "azure" in chunk_text_lower:
            boosted_score *= 1.10
            
        if has_question and chunk.metadata.section and "q&a" in chunk.metadata.section.lower():
            boosted_score *= 1.10
            
        results.append(SearchResult(
            score=boosted_score,
            text=chunk.text,
            metadata=chunk.metadata
        ))
        
    # Sort by score descending
    results.sort(key=lambda x: x.score, reverse=True)
    
    return results[:top_k]
