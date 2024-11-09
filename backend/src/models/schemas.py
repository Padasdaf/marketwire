from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class SentimentLabel(str, Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"

class AlertType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class UserBase(BaseModel):
    email: str
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str = Field(alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    watchlist: List[str] = []

class CompanyBase(BaseModel):
    symbol: str
    name: str
    sector: Optional[str] = None

class Company(CompanyBase):
    id: str = Field(alias="_id")
    subscribed_users: List[str] = []

class Article(BaseModel):
    id: str = Field(alias="_id")
    company_symbol: str
    title: str
    content: str
    url: str
    publish_date: datetime
    source: str
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[SentimentLabel] = None
    processed_date: Optional[datetime] = None

class Alert(BaseModel):
    id: str = Field(alias="_id")
    company_symbol: str
    type: AlertType
    message: str
    sentiment_score: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    notified_users: List[str] = []

class SentimentResponse(BaseModel):
    company_symbol: str
    sentiment_score: float
    sentiment_label: SentimentLabel
    recent_articles: List[Article]
    generated_at: datetime = Field(default_factory=datetime.utcnow)