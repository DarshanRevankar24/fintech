import yfinance as yf
from typing import Optional, List

# Basic mapping to speed up common requests in the demo instead of always polling yfinance.
COMMON_FALLBACK_MAP = {
    "TESLA": "TSLA",
    "AMAZON": "AMZN",
    "META": "META",
    "FACEBOOK": "META",
    "GOOGLE": "GOOGL",
    "ALPHABET": "GOOGL",
    "NETFLIX": "NFLX",
    "AMD": "AMD",
    "INTEL": "INTC"
}

def get_stock_price(ticker: str) -> Optional[float]:
    """
    Fetch the latest closing stock price using yfinance.
    Returns None if fetching fails.
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d")
        if not hist.empty:
            return round(float(hist['Close'].iloc[-1]), 2)
    except Exception as e:
        print(f"[ERROR] Failed to fetch price for {ticker}: {e}")
    return None

def fallback_search_ticker(company_name: str) -> Optional[str]:
    """
    Attempt to find a ticker for an unknown company.
    Since yfinance lacks a direct quick search in the API, we use a basic heuristic map
    for the hackathon demo.
    """
    name_upper = company_name.strip().upper()
    
    # Check if it looks exactly like a standard ticker (1-5 uppercase letters)
    if name_upper.isalpha() and len(name_upper) <= 5:
        return name_upper
        
    for key, ticker in COMMON_FALLBACK_MAP.items():
        if key in name_upper:
            return ticker
            
    return None
