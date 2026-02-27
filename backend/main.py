"""
Financial Explanation Assistant - FREE VERSION using Groq
100% FREE - 14,400 requests/day - SUPER FAST!
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal, Dict
from datetime import datetime, date, timedelta
from groq import Groq
from dotenv import load_dotenv  # Add this import
import os
import csv
import io
import json
import pandas as pd
import yfinance as yf

# Auth & DB imports
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import database
import models
import auth

# Initialize DB tables
models.Base.metadata.create_all(bind=database.engine)

# Load environment variables from .env file
load_dotenv()  # Add this line

# ============================================================================
# CONFIGURATION - 100% FREE with Groq (World's Fastest AI API)
# ============================================================================

app = FastAPI(
    title="Financial Explanation API",
    description="AI-powered portfolio explainer using Groq (Fastest AI)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the static frontend
app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")

# Configure Groq (FREE!)
# Get your free API key from: https://console.groq.com/keys
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class PortfolioHolding(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol", example="AAPL")
    shares: float = Field(..., gt=0, description="Number of shares owned")
    purchase_price: float = Field(..., gt=0, description="Price per share when purchased")
    purchase_date: date = Field(..., description="Date of purchase (YYYY-MM-DD)")
    current_price: Optional[float] = Field(None, gt=0, description="Current market price")
    
    @validator('ticker')
    def ticker_uppercase(cls, v):
        return v.upper().strip()

class ExplanationRequest(BaseModel):
    portfolio: List[PortfolioHolding] = Field(..., min_items=1)
    user_level: Literal["beginner", "intermediate", "expert"] = Field(default="beginner")
    include_tax_analysis: bool = Field(default=True)
    include_rebalancing: bool = Field(default=True)
    transcript_context: Optional[str] = Field(None)

# Auth schemas
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_name: str

class UserResponse(BaseModel):
    username: str
    email: str
    full_name: str

# Strict JSON LLM Response Models
class RebalancingIdea(BaseModel):
    action: str
    reason: str
    impact: str

class StockAnalysis(BaseModel):
    ticker: str
    performance_summary: str
    risk_signals_from_transcripts: List[str]
    tax_consideration: str
    citations: List[str]

class ExplanationResponse(BaseModel):
    greeting: str
    portfolio_summary: str
    key_takeaways: List[str]
    per_stock_analysis: List[StockAnalysis]
    tax_optimization_advice: str
    risk_score_explanation: str
    confidence_score: float
    action_plan: List[str]
    # Keep the original calculated metrics to return alongside the AI response
    portfolio_metrics: dict = Field(default_factory=dict)

# ============================================================================
# SERVICE LAYER - Using Groq (World's Fastest AI)
# ============================================================================

class PortfolioAnalyzer:
    """
    FREE version using Groq - World's Fastest AI API
    
    Why Groq?
    1. 100% FREE - 14,400 requests/day
    2. SUPER FAST - Fastest inference speed in the world
    3. High quality - Uses Llama 3.1 70B (open source powerhouse)
    4. No rate limit issues - Much higher limits than Gemini
    """
    
    def __init__(self, client):
        self.client = client
    
    def calculate_portfolio_metrics(self, holdings: List[PortfolioHolding]) -> dict:
        """Calculate portfolio statistics"""
        total_value = 0
        total_cost = 0
        holdings_value = {}
        
        for holding in holdings:
            current_price = holding.current_price or holding.purchase_price
            position_value = holding.shares * current_price
            position_cost = holding.shares * holding.purchase_price
            
            total_value += position_value
            total_cost += position_cost
            holdings_value[holding.ticker] = position_value
        
        sector_allocation = self._estimate_sector_allocation(holdings_value)
        
        return {
            "total_value": round(total_value, 2),
            "total_cost_basis": round(total_cost, 2),
            "unrealized_gain": round(total_value - total_cost, 2),
            "unrealized_gain_percent": round((total_value - total_cost) / total_cost * 100, 2) if total_cost > 0 else 0,
            "holdings_count": len(holdings),
            "largest_position": max(holdings_value, key=holdings_value.get) if holdings_value else "N/A",
            "largest_position_percent": round(max(holdings_value.values()) / total_value * 100, 2) if total_value > 0 else 0,
            "sector_allocation": sector_allocation
        }
    
    def _estimate_sector_allocation(self, holdings_value: dict) -> dict:
        """Estimate sector allocation based on ticker"""
        tech_stocks = ["AAPL", "MSFT", "GOOGL", "NVDA", "META", "AMZN", "TSLA"]
        finance_stocks = ["JPM", "BAC", "GS", "MS", "V", "MA"]
        
        tech_value = sum(v for k, v in holdings_value.items() if k in tech_stocks)
        finance_value = sum(v for k, v in holdings_value.items() if k in finance_stocks)
        other_value = sum(v for k, v in holdings_value.items() 
                         if k not in tech_stocks and k not in finance_stocks)
        
        total = tech_value + finance_value + other_value
        
        return {
            "Technology": round(tech_value / total, 2) if total > 0 else 0,
            "Finance": round(finance_value / total, 2) if total > 0 else 0,
            "Other": round(other_value / total, 2) if total > 0 else 0
        }
    
    def generate_explanation(
        self,
        holdings: List[PortfolioHolding],
        metrics: dict,
        user_name: str,
        user_level: str,
        transcript_context: Optional[str] = None
    ) -> str:
        """
        Call Groq API (FREE and FAST!) to generate explanation
        
        Groq uses OpenAI-compatible API - very simple!
        Enforces strict JSON output.
        """
        
        # We can calculate some basic tax string conceptually to pass as input
        tax_summary = "Tax implications depend on holding period. Assets held >1 yr are subject to long term capital gains."
        risk_model_output = "Moderate risk calculated via standard volatility metrics."
        rag_context = transcript_context if transcript_context else "No relevant earnings call transcripts retrieved."
        
        portfolio_metrics_str = self._format_portfolio_for_prompt(holdings, metrics)
        
        prompt = f"""You are a professional AI Financial Advisor specializing in portfolio analysis, tax-aware investment strategy, and risk assessment grounded in earnings call transcripts.

Your responsibilities:
- Analyze structured portfolio metrics.
- Interpret tax implications (STCG vs LTCG).
- Evaluate risk using provided quantitative signals.
- Use ONLY the provided transcript excerpts as factual grounding.
- Avoid hallucination or adding external assumptions.
- Maintain a professional, neutral, and analytical tone.

You must return STRICTLY VALID JSON.
Do not use markdown.
Do not add commentary outside JSON.
Do not invent data not present in the inputs.

==============================
CLIENT INFORMATION
==============================

Client Name: {user_name}
Experience Level: {user_level}

Portfolio Metrics:
{portfolio_metrics_str}

Tax Analysis:
{tax_summary}

Risk Model Output:
{risk_model_output}

Retrieved Transcript Evidence:
{rag_context}

==============================
ADAPT RESPONSE BASED ON EXPERIENCE LEVEL
==============================

If Experience Level is "beginner":
- Use simple language.
- Avoid heavy financial jargon.
- Explain financial concepts briefly.
- Focus on clarity and guidance.

If Experience Level is "intermediate":
- Use moderate financial terminology.
- Explain important metrics like margin, allocation, concentration.
- Provide balanced analytical depth.

If Experience Level is "expert":
- Use technical financial terminology.
- Discuss margin trends, EPS implications, concentration risk, and sector exposure precisely.
- Provide deeper analytical reasoning and structured insights.

==============================
RESPONSE REQUIREMENTS
==============================

1. Greet the client professionally using their name.
2. Provide a concise portfolio summary.
3. Highlight key takeaways.
4. For each stock:
   - Summarize performance.
   - Mention transcript-based risk signals.
   - Reference citations using provided metadata IDs.
   - Explain tax considerations if sold today.
5. Clearly explain risk score breakdown using provided risk components.
6. Provide tax optimization insight (e.g., holding period benefits).
7. Provide a calculation for `confidence_score` as a float between 0.0 and 1.0. This score MUST dynamically reflect:
   - Completeness of the user's portfolio data
   - Quality and relevance of the retrieved transcript evidence 
   - Clarity of the market signals
   DO NOT hardcode this to 0.2 or 0.0. Calculate a real estimate (e.g., 0.85, 0.62).
8. Provide a short, actionable plan (not financial advice disclaimer heavy).

If transcript evidence is insufficient, clearly state that insight is limited.

==============================
STRICT OUTPUT FORMAT
==============================

Return ONLY this JSON structure exactly:

{{
  "greeting": "",
  "portfolio_summary": "",
  "key_takeaways": [],
  "per_stock_analysis": [
    {{
      "ticker": "",
      "performance_summary": "",
      "risk_signals_from_transcripts": [],
      "tax_consideration": "",
      "citations": []
    }}
  ],
  "tax_optimization_advice": "",
  "risk_score_explanation": "",
  "confidence_score": 0.85, 
  "action_plan": []
}}
"""

        try:
            print(f"[DEBUG] Calling Groq API...")
            
            # Call Groq - Uses OpenAI-compatible API format
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # Updated to current model
                messages=[
                    {"role": "system", "content": "You are a professional AI Financial Advisor. Output only raw JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2, # Lower temp for more stable JSON
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            print(f"[DEBUG] Groq response received")
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"[ERROR] Groq API failed: {str(e)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Groq API error: {str(e)}")
    
    def _format_portfolio_for_prompt(self, holdings: List[PortfolioHolding], metrics: dict) -> str:
        """Format portfolio data for prompt"""
        lines = [
            f"Total Portfolio Value: ${metrics['total_value']:,.2f}",
            f"Total Gain/Loss: ${metrics['unrealized_gain']:,.2f} ({metrics['unrealized_gain_percent']:+.1f}%)",
            f"Number of Holdings: {metrics['holdings_count']}",
            f"\nLargest Position: {metrics['largest_position']} ({metrics['largest_position_percent']:.1f}% of portfolio)",
            f"\nSector Allocation:"
        ]
        
        for sector, allocation in metrics['sector_allocation'].items():
            if allocation > 0:
                lines.append(f"  - {sector}: {allocation*100:.0f}%")
        
        lines.append("\nIndividual Holdings:")
        for holding in holdings:
            current = holding.current_price or holding.purchase_price
            gain = (current - holding.purchase_price) * holding.shares
            lines.append(
                f"  - {holding.ticker}: {holding.shares} shares @ ${current:.2f} "
                f"(gain: ${gain:,.2f})"
            )
        
        return "\n".join(lines)
    
    def generate_rebalancing_ideas(
        self,
        holdings: List[PortfolioHolding],
        metrics: dict,
        explanation: str
    ) -> List[RebalancingIdea]:
        """Generate rebalancing suggestions using Groq"""
        
        prompt = f"""Based on this portfolio analysis:

{explanation}

Portfolio metrics:
- Largest position: {metrics['largest_position']} at {metrics['largest_position_percent']:.1f}%
- Sector allocation: {json.dumps(metrics['sector_allocation'])}

Suggest 2-3 conceptual rebalancing ideas for diversification.
For each idea, provide in this EXACT format (one line per idea):
ACTION | REASON | IMPACT

Example:
Reduce tech exposure by 10% | Over-concentration in single sector | Improves diversification

Now provide your suggestions:"""

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # Updated to current model
                messages=[
                    {"role": "system", "content": "You are a financial advisor providing rebalancing suggestions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            # Parse response
            ideas = []
            lines = response.choices[0].message.content.strip().split('\n')
            
            for line in lines:
                if '|' in line:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) == 3:
                        ideas.append(RebalancingIdea(
                            action=parts[0],
                            reason=parts[1],
                            impact=parts[2]
                        ))
            
            return ideas if ideas else [RebalancingIdea(
                action="Review portfolio allocation",
                reason="Ensure diversification across sectors",
                impact="Reduces concentration risk"
            )]
        
        except Exception as e:
            return [RebalancingIdea(
                action="Review portfolio allocation",
                reason="Ensure diversification across sectors",
                impact="Reduces concentration risk"
            )]

# ============================================================================
# API ROUTES
# ============================================================================

analyzer = PortfolioAnalyzer(client)

from chatbot.router import router as chatbot_router
app.include_router(chatbot_router)

from rag_vectorless import SearchQuery, SearchResponse, search_index, build_index_if_needed, generate_manifest_template

@app.on_event("startup")
def on_startup():
    build_index_if_needed()

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/rag/search", response_model=SearchResponse)
def rag_search(query: SearchQuery):
    results = search_index(query)
    return SearchResponse(query=query.query, results=results)

@app.post("/rag/rebuild")
def rag_rebuild():
    # Force rebuild by passing a flag or just deleting the file state?
    # Actually, build_index_if_needed respects the needs_rebuild() function.
    # To force, we can call global_index.build directly.
    from rag_vectorless import global_index
    global_index.build("./transcripts")
    return {"status": "success", "message": "Index rebuilt"}

@app.get("/rag/manifest-template")
def rag_manifest_template():
    return generate_manifest_template("./transcripts")



@app.post("/api/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/api/login", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "user_name": user.full_name}

@app.post("/api/portfolio/save")
def save_portfolio(
    portfolio: List[PortfolioHolding],
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    # Clear old holdings
    db.query(models.Holding).filter(models.Holding.owner_id == current_user.id).delete()
    
    # Add new holdings
    for holding in portfolio:
        db_holding = models.Holding(
            ticker=holding.ticker,
            shares=holding.shares,
            purchase_price=holding.purchase_price,
            purchase_date=holding.purchase_date.strftime("%Y-%m-%d"),
            owner_id=current_user.id
        )
        db.add(db_holding)
    db.commit()
    return {"message": "Portfolio saved successfully"}

@app.get("/api/portfolio/get", response_model=List[PortfolioHolding])
def get_portfolio(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    holdings = db.query(models.Holding).filter(models.Holding.owner_id == current_user.id).all()
    # Convert DB models to Pydantic models for response
    return [
        PortfolioHolding(
            ticker=h.ticker,
            shares=h.shares,
            purchase_price=h.purchase_price,
            purchase_date=h.purchase_date
        ) for h in holdings
    ]

@app.post("/api/explain", response_model=ExplanationResponse)
async def explain_portfolio(
    request: ExplanationRequest,
    current_user: models.User = Depends(auth.get_current_user)
):
    """Main endpoint - returns strict structured JSON"""
    
    try:
        print(f"[DEBUG] Received request with {len(request.portfolio)} holdings for user {current_user.full_name}")
        
        # Helper to resolve company name to ticker if it's not a standard symbol
        def resolve_ticker(name_or_ticker: str) -> str:
            name_str = name_or_ticker.strip().upper()
            # If it looks like a standard ticker (1-5 uppercase letters), return it
            if name_str.isalpha() and len(name_str) <= 5:
                return name_str
            # Otherwise, try to use yfinance to search for the most likely ticker
            try:
                # yfinance currently doesn't have a direct "search" endpoint available reliably in all versions, 
                # but we can try fetching a ticker to see if it implicitly matched, or rely on a hardcoded map for common requests during the demo
                common_map = {
                    "APPLE": "AAPL", "MICROSOFT": "MSFT", "NVIDIA": "NVDA", 
                    "TESLA": "TSLA", "AMAZON": "AMZN", "META": "META",
                    "FACEBOOK": "META", "GOOGLE": "GOOGL", "ALPHABET": "GOOGL",
                    "NETFLIX": "NFLX", "AMD": "AMD", "INTEL": "INTC"
                }
                for key in common_map:
                    if key in name_or_ticker.upper():
                        return common_map[key]
                return name_str # Fallback to giving what they typed
            except Exception:
                return name_str
                
        # Fetch real-time prices for holdings if missing
        updated_holdings = []
        for holding in request.portfolio:
            resolved_symbol = resolve_ticker(holding.ticker)
            # Update the holding so the rest of the app uses the valid ticker
            holding.ticker = resolved_symbol
            
            if holding.current_price is None:
                try:
                    stock = yf.Ticker(resolved_symbol)
                    hist = stock.history(period="1d")
                    if not hist.empty:
                        holding.current_price = round(float(hist['Close'].iloc[-1]), 2)
                    else:
                        holding.current_price = holding.purchase_price
                except Exception as e:
                    print(f"[WARNING] Could not fetch price for {holding.ticker}: {e}")
                    holding.current_price = holding.purchase_price
            updated_holdings.append(holding)
            
        request.portfolio = updated_holdings
        metrics = analyzer.calculate_portfolio_metrics(request.portfolio)
        
        explanation_json = analyzer.generate_explanation(
            holdings=request.portfolio,
            metrics=metrics,
            user_name=current_user.full_name, # Injected from DB
            user_level=request.user_level,
            transcript_context=request.transcript_context
        )
        print(f"[DEBUG] Explanation generated")
        
        # Parse JSON output from Groq
        import json
        structured_data = json.loads(explanation_json)
        
        # Override the LLM's confidence_score with deterministic analytics
        try:
            # 1. Base confidence (50%)
            calc_confidence = 0.50
            
            # 2. Portfolio Size factor (+ up to 25%)
            # More holdings = we have more data to diversify risk analysis
            num_holdings = metrics.get('holdings_count', 1)
            size_factor = min(0.25, (num_holdings / 10.0) * 0.25)
            calc_confidence += size_factor
            
            # 3. Sector Diversification factor (+ up to 25%)
            # Less concentration in the top position = more confident overall analysis
            top_pos_percent = metrics.get('largest_position_percent', 100)
            if top_pos_percent < 100:
                # If they are 100% in one stock, 0 bonus. 
                # If they are 20% in one stock, max bonus.
                diversification_bonus = min(0.25, ((100 - top_pos_percent) / 80.0) * 0.25)
                calc_confidence += diversification_bonus
                
            # Cap safely at 99%
            calc_confidence = round(min(0.99, calc_confidence), 2)
            
            structured_data['confidence_score'] = calc_confidence
        except Exception as override_err:
            print(f"[WARNING] Failed to override confidence score: {override_err}")
        
        # Merge metrics back into the final response
        structured_data['portfolio_metrics'] = metrics
        
        return ExplanationResponse(**structured_data)
    
    except json.JSONDecodeError:
        print(f"[ERROR] LLM Failed to return valid JSON")
        raise HTTPException(status_code=500, detail="Failed to parse AI response into structured format.")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

# Mount the static frontend directory
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
