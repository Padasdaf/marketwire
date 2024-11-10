from fastapi import FastAPI, Depends,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import router 
# from celery import Celery
# from celery.schedules import crontab
from src.models.database import db
from src.utils.config import get_settings
from src.services.news_scraper import NewsScraperService
from src.services.sentiment_analyzer import SentimentAnalyzer
from src.utils.logger import logger 
# from src.services.alert_manager import AlertManager

settings = get_settings()

# Initialize FastAPI app
app = FastAPI(title="Stock Sentiment Analysis API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with actual frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
news_scraper = NewsScraperService()
sentiment_analyzer = SentimentAnalyzer()
# Initialize Celery
# celery_app = Celery(
#     'tasks',
#     broker=settings.celery_broker_url,
#     backend=settings.celery_result_backend
# )

# Configure Celery periodic tasks
# celery_app.conf.beat_schedule = {
#     'scrape-news-every-hour': {
#         'task': 'scrape_news',
#         'schedule': crontab(minute=0)  # Run every hour
#     },
#     'analyze-sentiment-every-15-minutes': {
#         'task': 'analyze_sentiment',
#         'schedule': crontab(minute='*/15')  # Run every 15 minutes
#     },
#     'process-alerts-every-5-minutes': {
#         'task': 'process_alerts',
#         'schedule': crontab(minute='*/5')  # Run every 5 minutes
#     }
# }

# # Celery tasks
# @celery_app.task(name='scrape_news')
# def scrape_news():
#     """Celery task to scrape news articles"""
#     import asyncio
#     asyncio.run(news_scraper.run_scraper())

# @celery_app.task(name='analyze_sentiment')
# def analyze_sentiment():
#     """Celery task to analyze sentiment of news articles"""
#     import asyncio
#     asyncio.run(sentiment_analyzer.analyze_articles())

# @celery_app.task(name='process_alerts')
# def process_alerts():
#     """Celery task to process and send alerts"""
#     import asyncio
#     asyncio.run(alert_manager.process_alerts())

app.include_router(router, prefix="/api")
# FastAPI startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        # Initialize database connection
        db.connect_to_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise e

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    try:
        # Clean up database connection
        db.client = None
        logger.info("Database connection cleaned up")
    except Exception as e:
        logger.error(f"Error cleaning up database: {str(e)}")
        raise e
# Import and include API routes
from src.api.routes import router as api_router
app.include_router(api_router, prefix="/api")

@app.get("/company-news/{symbol}")
async def get_company_news(symbol: str, days: int = 7):
    try:
        articles = await news_scraper.fetch_company_news(symbol, days)
        
        # Add sentiment analysis
        for article in articles:
            if article.content:
                sentiment_label, sentiment_score = sentiment_analyzer.analyze_text(article.content)
                article.sentiment_label = sentiment_label
                article.sentiment_score = sentiment_score
                
        return articles
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Root endpoint
@app.get("/")
def root():
    return {"message": "Stock Sentiment Analysis API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)