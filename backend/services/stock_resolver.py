import re
from typing import List

# Part 1: Static stock registry (for hackathon demo)
stock_registry = {
    "AAPL": {
        "aliases": ["apple", "apple inc", "apple corporation"],
        "company_name": "Apple Inc"
    },
    "MSFT": {
        "aliases": ["microsoft", "microsoft corp", "microsoft corporation"],
        "company_name": "Microsoft Corporation"
    },
    "NVDA": {
        "aliases": ["nvidia", "nvidia corp", "nvidia corporation"],
        "company_name": "NVIDIA Corporation"
    }
}

def build_alias_map():
    """Builds a flat mapping of lowercase regex-compatible patterns to canonical tickers."""
    alias_map = {}
    for ticker, data in stock_registry.items():
        # Map the exact canonical ticker format (lowercase for ease of matching)
        alias_map[ticker.lower()] = ticker
        
        # Map all aliases
        for alias in data["aliases"]:
            alias_map[alias.lower()] = ticker
            
    return alias_map

ALIAS_MAP = build_alias_map()

def resolve_stock(user_input_text: str) -> List[str]:
    """
    Parses user input text to resolve stock references.
    Behavior:
    - Case insensitive
    - Detect both ticker and company name
    - Return a list of unique canonical ticker(s)
    - If none found, return empty list
    - Uses regex word boundary matching to avoid false positives.
    """
    found_tickers = set()
    text_lower = user_input_text.lower()
    
    # Sort aliases by length descending so that longer names match first 
    # (e.g. "apple inc" matches before "apple")
    sorted_aliases = sorted(ALIAS_MAP.keys(), key=len, reverse=True)
    
    for alias in sorted_aliases:
        # Regex explanation:
        # \b ensures we are matching whole words only, avoiding partial matches (e.g. 'pineapple' won't match 'apple')
        # re.escape is used because some aliases might have special regex characters, though ours don't right now
        pattern = r'\b' + re.escape(alias) + r'\b'
        
        if re.search(pattern, text_lower):
            found_tickers.add(ALIAS_MAP[alias])
            # To prevent double matching like matching "apple" after matching "apple inc"
            # we could theoretically remove the matched string, but since we use a set it's fine 
            # as it will just add the same canonical ticker again.
            
    return list(found_tickers)
