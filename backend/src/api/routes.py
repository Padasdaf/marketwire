from fastapi import APIRouter, HTTPException, Depends
from src.models.schemas import SentimentResponse, SentimentLabel, Article
from src.models.database import db
from typing import List
from datetime import datetime

router = APIRouter()

@router.get("/stocks")
async def get_stocks():
    try:
        companies = await db.get_companies()
        return {"stocks": [company["symbol"] for company in companies]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sentiment/{stock_symbol}")
async def get_sentiment(stock_symbol: str):
    try:
        # Get company details
        company = await db.get_company(stock_symbol)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
            
        # Get recent articles
        articles = await db.get_company_articles(stock_symbol, limit=5)
        
        # Calculate average sentiment
        if articles:
            avg_sentiment = sum(article["sentiment_score"] for article in articles) / len(articles)
            sentiment_label = SentimentLabel.POSITIVE if avg_sentiment > 0.5 else \
                            SentimentLabel.NEGATIVE if avg_sentiment < -0.5 else \
                            SentimentLabel.NEUTRAL
        else:
            avg_sentiment = 0
            sentiment_label = SentimentLabel.NEUTRAL
            
        return SentimentResponse(
            company_symbol=stock_symbol,
            sentiment_score=avg_sentiment,
            sentiment_label=sentiment_label,
            recent_articles=articles,
            generated_at=datetime.utcnow()
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))