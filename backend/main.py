from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import asyncio

app = FastAPI()

class CompanySubscription(BaseModel):
    symbol: str
    user_id: int
    alert_threshold: float = 0.5

@app.post("/api/companies/subscribe")
async def subscribe_to_company(subscription: CompanySubscription):
    try:
        await db.companies.insert_one(subscription.dict())
        # Initialize background monitoring for this company
        await start_monitoring(subscription.symbol)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/sentiment/{company_symbol}")
async def get_company_sentiment(company_symbol: str):
    news_scraper = NewsScraperService()
    sentiment_analyzer = SentimentAnalyzer()
    
    articles = await news_scraper.fetch_company_news(company_symbol)
    sentiment = await sentiment_analyzer.analyze_articles(articles)
    
    return {
        "company": company_symbol,
        "sentiment_score": sentiment.aggregate_score,
        "recent_articles": articles[:5]
    }
