from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class FinancialStatus(BaseModel):
    category: str  # "Poor", "Fair", "Good", "Excellent"
    income: int
    savings: int
    monthly_investment: int

class CustomerRequest(BaseModel):
    customer_id: str
    name: str

class CustomerProfile(BaseModel):
    customer_id: str
    name: str
    age: int
    investment_tendency: str  # "Conservative", "Moderate", "Aggressive"
    financial_status: FinancialStatus
    has_etf: bool
    current_etf_holdings: Optional[str] = None
    risk_tolerance: str  # "Low", "Medium", "High"
    investment_horizon: str  # "Short-term (1-3 years)", "Medium-term (3-5 years)", "Long-term (5+ years)"
    created_at: datetime

class RebalanceReportRequest(BaseModel):
    customer_id: str
    current_etf_holdings: str
    risk_tolerance: str
    age: int
    financial_status: Dict[str, Any]

class ETFRecommendation(BaseModel):
    recommendations: List[str]
    reasons: str
    portfolio_analysis: Optional[str] = None
    rebalancing_needed: Optional[bool] = None
    rebalancing_suggestions: Optional[List[str]] = None

class RebalanceReport(BaseModel):
    report: str
    performance_analysis: str
    rebalancing_needed: bool
    suggestions: str
