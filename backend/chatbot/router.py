from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from services.stock_resolver import resolve_stock
from services.stock_service import get_stock_price, fallback_search_ticker
from rag_vectorless.search import search_index
from rag_vectorless.schemas import SearchQuery

router = APIRouter(
    prefix="/chat",
    tags=["chatbot"]
)

class ChatMessageRequest(BaseModel):
    message: str = Field(..., description="The user's question or message")
    top_k_sources: int = Field(5, description="Number of transcript excerpts to retrieve per stock")

class ChatMessageResponse(BaseModel):
    reply: str
    detected_stocks: List[str]
    sources: List[Any]

def call_llm(prompt: str) -> str:
    """Helper to mock/call Groq LLM API.
    Since main.py has `client` initialized, we reuse it or do a late import."""
    try:
        from main import client
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a professional Financial Chatbot. Answer the user's query factually using the provided context. If no context helps, use your general knowledge but note the lack of retrieved context."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[ERROR] LLM call failed in router: {e}")
        return "Sorry, I encountered an error generating the response."

@router.post("/message", response_model=ChatMessageResponse)
def handle_chat_message(request: ChatMessageRequest):
    user_text = request.message
    
    # PART 1 & 2: Resolve stocks from text
    resolved_tickers = resolve_stock(user_text)
    
    all_sources = []
    prices_info = []
    
    # Optional Fallback (Bonus)
    if not resolved_tickers:
        # User might be asking a generic question or a tech stock not in registry
        attempted_ticker = fallback_search_ticker(user_text)
        if attempted_ticker:
            resolved_tickers.append(attempted_ticker)
            
    if len(resolved_tickers) > 0:
        # We found one or more stocks. Attempt RAG & Price fetch.
        for ticker in resolved_tickers:
            # 1. Fetch Price
            price = get_stock_price(ticker)
            if price:
                prices_info.append(f"{ticker} Current Price: ${price}")
                
            # 2. Fetch RAG Context
            # Depending on how the transcripts are matched, we specify the lower or upper ticker.
            # Usually index metadata company is either lowercase or whatever the loader decides.
            # From loader.py: "NVDA", "AAPL", "MSFT" (We updated this to Canonical Uppercase)
            company_filter = ticker.upper() 
            rag_req = SearchQuery(
                query=user_text,
                top_k=request.top_k_sources,
                filters={"company": company_filter}
            )
            rag_results = search_index(rag_req)
            all_sources.extend(rag_results)
            
        # Format the RAG context string
        context_str = "\n\n".join([f"[{result.metadata.company.upper()}] {result.text}" for result in all_sources])
        price_str = "\n".join(prices_info)
        
        prompt = f"""User asks: "{user_text}"
        
Detected Stocks: {', '.join(resolved_tickers)}
Real-time Price Info:
{price_str}

Context from latest earnings transcripts:
{context_str}

Please answer the user's question directly and concisely, using the context provided.
"""
        reply = call_llm(prompt)
        
        return ChatMessageResponse(
            reply=reply,
            detected_stocks=resolved_tickers,
            sources=[res.dict() for res in all_sources]
        )
        
    else:
        # PART 4: Generic queries (No stocks resolved)
        prompt = f"""User asks: "{user_text}"
        
Note: No specific stock tickets were detected. Answer generally or request clarification if they meant a specific company.
Currently officially supported stocks mostly include AAPL, MSFT, and NVDA.
"""
        reply = call_llm(prompt)
        return ChatMessageResponse(
            reply=reply,
            detected_stocks=[],
            sources=[]
        )
