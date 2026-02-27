"""
Financial Explanation Assistant - FREE VERSION using Groq
100% FREE - 14,400 requests/day - SUPER FAST!
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
from datetime import datetime, date
from groq import Groq
from dotenv import load_dotenv  # Add this import
import os
import csv
import io
import json
import pandas as pd
import yfinance as yf

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

class TaxImpact(BaseModel):
    holding: str
    gain_loss: float
    holding_period_days: int
    tax_type: Literal["short_term", "long_term"]
    estimated_tax_rate: float
    estimated_tax: float

class RebalancingIdea(BaseModel):
    action: str
    reason: str
    impact: str

class ExplanationResponse(BaseModel):
    explanation: str
    risk_highlights: List[str] = Field(default_factory=list)
    positives: List[str] = Field(default_factory=list)
    tax_impacts: Optional[List[TaxImpact]] = None
    rebalancing_ideas: Optional[List[RebalancingIdea]] = None
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
    
    def calculate_tax_impacts(self, holdings: List[PortfolioHolding]) -> List[TaxImpact]:
        """Calculate tax implications"""
        tax_impacts = []
        today = datetime.now().date()
        
        for holding in holdings:
            current_price = holding.current_price or holding.purchase_price
            gain_loss = (current_price - holding.purchase_price) * holding.shares
            holding_days = (today - holding.purchase_date).days
            
            if holding_days < 365:
                tax_type = "short_term"
                tax_rate = 0.24
            else:
                tax_type = "long_term"
                tax_rate = 0.15
            
            estimated_tax = gain_loss * tax_rate if gain_loss > 0 else 0
            
            tax_impacts.append(TaxImpact(
                holding=holding.ticker,
                gain_loss=round(gain_loss, 2),
                holding_period_days=holding_days,
                tax_type=tax_type,
                estimated_tax_rate=tax_rate,
                estimated_tax=round(estimated_tax, 2)
            ))
        
        return tax_impacts
    
    def generate_explanation(
        self,
        holdings: List[PortfolioHolding],
        metrics: dict,
        user_level: str,
        transcript_context: Optional[str] = None
    ) -> str:
        """
        Call Groq API (FREE and FAST!) to generate explanation
        
        Groq uses OpenAI-compatible API - very simple!
        """
        
        level_instructions = {
            "beginner": "Explain in simple terms, avoid jargon, use analogies. Be friendly and educational.",
            "intermediate": "Use standard financial terminology but explain complex concepts clearly.",
            "expert": "Use technical language and focus on metrics, ratios, and data-driven insights."
        }
        
        portfolio_summary = self._format_portfolio_for_prompt(holdings, metrics)
        
        prompt = f"""You are a financial advisor helping someone understand their portfolio.

User level: {user_level}
Instructions: {level_instructions[user_level]}

Portfolio Analysis:
{portfolio_summary}

{"Context from company transcripts: " + transcript_context if transcript_context else ""}

Please provide:
1. Overall portfolio assessment (2-3 sentences)
2. Key strengths (2-3 points)
3. Main risks or concerns (2-3 points)
4. Outlook based on current holdings

Keep it concise and actionable."""

        try:
            print(f"[DEBUG] Calling Groq API...")
            
            # Call Groq - Uses OpenAI-compatible API format
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # Updated to current model
                messages=[
                    {"role": "system", "content": "You are a helpful financial advisor."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
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

@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Financial Explanation API (FREE with Groq - World's Fastest AI) is running",
        "docs": "/docs",
        "cost": "100% FREE - 14,400 requests/day",
        "speed": "⚡ FASTEST AI API in the world"
    }

@app.post("/api/explain", response_model=ExplanationResponse)
async def explain_portfolio(request: ExplanationRequest):
    """Main endpoint - completely FREE with Groq"""
    
    try:
        print(f"[DEBUG] Received request with {len(request.portfolio)} holdings")
        
        # Fetch real-time prices for holdings if missing
        updated_holdings = []
        for holding in request.portfolio:
            if holding.current_price is None:
                try:
                    stock = yf.Ticker(holding.ticker)
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
        print(f"[DEBUG] Metrics calculated")
        
        explanation = analyzer.generate_explanation(
            holdings=request.portfolio,
            metrics=metrics,
            user_level=request.user_level,
            transcript_context=request.transcript_context
        )
        print(f"[DEBUG] Explanation generated")
        
        tax_impacts = None
        if request.include_tax_analysis:
            tax_impacts = analyzer.calculate_tax_impacts(request.portfolio)
        
        rebalancing_ideas = None
        if request.include_rebalancing:
            rebalancing_ideas = analyzer.generate_rebalancing_ideas(
                holdings=request.portfolio,
                metrics=metrics,
                explanation=explanation
            )
        
        lines = explanation.split('\n')
        risk_highlights = [l.strip('- ').strip() for l in lines if 'risk' in l.lower() or 'concern' in l.lower()][:3]
        positives = [l.strip('- ').strip() for l in lines if 'strength' in l.lower() or 'positive' in l.lower()][:3]
        
        return ExplanationResponse(
            explanation=explanation,
            risk_highlights=risk_highlights,
            positives=positives,
            tax_impacts=tax_impacts,
            rebalancing_ideas=rebalancing_ideas,
            portfolio_metrics=metrics
        )
    
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"[ERROR] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

