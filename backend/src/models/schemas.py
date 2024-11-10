from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from enum import Enum
from uuid import UUID

class SentimentLabel(str, Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"

class AlertType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class Article(BaseModel):
    url: str
    title: str
    content: str
    publish_date: datetime
    source: str
    company_symbol: str
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @validator('sentiment_score')
    def validate_sentiment_score(cls, v):
        if v is not None and not (-1.0 <= v <= 1.0):
            raise ValueError('Sentiment score must be between -1.0 and 1.0')
        return v

    @validator('sentiment_label')
    def validate_sentiment_label(cls, v):
        if v is not None and v.lower() not in ['positive', 'negative', 'neutral']:
            raise ValueError('Invalid sentiment label')
        return v.lower()

class UserTable(BaseModel):
    id: UUID
    name: str
    email: str                      
    plan: str
    stripe: str  # Changed from stripe_id to stripe to match the table

class Company(BaseModel):
    id: UUID
    price: float
    symbol: str
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: int  # Changed to int4 as per your schema
    class Config:
        from_attributes = True 

class UserCompanyPreference(BaseModel):
    id: UUID
    user_id: UUID
    company_symbol: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SentimentAlert(BaseModel):
    id: UUID
    user_id: UUID
    company_symbol: str
    sentiment_score: float
    alert_type: str  # Changed from enum to text to match the table
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Response models
class SentimentResponse(BaseModel):
    company_symbol: str
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    sentiment_label: str
    recent_articles: List[Article]
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    @validator('sentiment_label')
    def validate_sentiment_label(cls, v):
        if v.lower() not in ['positive', 'negative', 'neutral']:
            raise ValueError('Invalid sentiment label')
        return v.lower()