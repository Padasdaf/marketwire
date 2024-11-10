from fastapi import APIRouter, HTTPException, Depends
from src.models.schemas import SentimentResponse, SentimentLabel, Article, Company
from src.models.database import db
from src.services.sentiment_analyzer import sentiment_analyzer
import asyncio
import uuid
from datetime import datetime, timedelta 
from src.services.news_scraper import NewsScraperService
from src.utils.logger import logger
from typing import List


router = APIRouter()

@router.get("/companies", response_model=List[Company], tags=['companies'])
def get_companies():
    """Get all companies from the database"""
    if not db.client:
        db.connect_to_database()
    
    try:
        companies = db.get_companies()
        print(f"Retrieved companies: {companies}")  # Debug print
        if not companies:
            return []
        return companies
    except Exception as e:
        print(f"Error in get_companies route: {str(e)}")  # Debug print
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    
@router.get("/stocks")
async def get_stocks():
    try:
        companies = await db.get_companies()
        return {"stocks": [company["symbol"] for company in companies]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @router.get("/sentiment/{stock_symbol}")
# async def get_sentiment(stock_symbol: str):
#     try:
#         # Get company details
#         company = await db.get_company(stock_symbol)
#         if not company:
#             raise HTTPException(status_code=404, detail="Company not found")
            
#         # Get recent articles
#         articles = await db.get_company_articles(stock_symbol, limit=5)
        
#         # Calculate average sentiment
#         if articles:
#             avg_sentiment = sum(article["sentiment_score"] for article in articles) / len(articles)
#             sentiment_label = SentimentLabel.POSITIVE if avg_sentiment > 0.5 else \
#                             SentimentLabel.NEGATIVE if avg_sentiment < -0.5 else \
#                             SentimentLabel.NEUTRAL
#         else:
#             avg_sentiment = 0
#             sentiment_label = SentimentLabel.NEUTRAL
            
#         return SentimentResponse(
#             company_symbol=stock_symbol,
#             sentiment_score=avg_sentiment,
#             sentiment_label=sentiment_label,
#             recent_articles=articles,
#             generated_at=datetime.utcnow()
#         )
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@router.get("/sentiment/{stock_symbol}", response_model=SentimentResponse)
async def get_sentiment(stock_symbol: str):
    news_scraper = NewsScraperService()
    try:
        # 1. Verify company exists
        company = db.get_company(stock_symbol.upper())
        if not company:
            raise HTTPException(
                status_code=404,
                detail=f"Company with symbol {stock_symbol} not found"
            )

        # 2. Get existing articles from database
        existing_articles = db.get_company_articles(stock_symbol.upper(), days_back=7)
        
        # 3. Fetch new articles if we don't have enough recent ones
        if len(existing_articles) < 5:
            # Initialize services
            new_articles = await news_scraper.fetch_company_news(stock_symbol, days_back=7)
            
            # Analyze and store new articles
            for article in new_articles:
                if article and article.title and article.content:  # Add null checks
                    text = f"{article.title} {article.content}"
                    label, score = sentiment_analyzer.analyze_text(text)
                    
                    article_data = {
                        "id": str(uuid.uuid4()),
                        "company_symbol": stock_symbol.upper(),
                        "title": article.title,
                        "content": article.content,
                        "url": article.url,
                        "source": article.source,
                        "publish_date": article.publish_date,
                        "sentiment_score": score,
                        "sentiment_label": label,
                        "created_at": datetime.utcnow()
                    }
                    
                    # Store in database
                    stored_article = db.store_article(article_data)
                    if stored_article:
                        existing_articles.append(stored_article)

        # 4. Calculate average sentiment from all articles
        if existing_articles:
            total_sentiment = sum(float(article.get("sentiment_score", 0)) for article in existing_articles)
            avg_sentiment = total_sentiment / len(existing_articles)
            
            sentiment_label = (
                SentimentLabel.POSITIVE if avg_sentiment > 0.2
                else SentimentLabel.NEGATIVE if avg_sentiment < -0.2
                else SentimentLabel.NEUTRAL
            )
        else:
            avg_sentiment = 0.0
            sentiment_label = SentimentLabel.NEUTRAL

        return SentimentResponse(
            company_symbol=stock_symbol.upper(),
            sentiment_score=round(avg_sentiment, 3),
            sentiment_label=sentiment_label,
            recent_articles=existing_articles[:5],
            generated_at=datetime.utcnow()
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error in get_sentiment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await news_scraper.close()