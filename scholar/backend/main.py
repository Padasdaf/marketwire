from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from celery import Celery
from celery.schedules import crontab
from .database import db
from .utils.config import get_settings
from .services.news_scraper import news_scraper
from .services.sentiment_analyzer import sentiment_analyzer
from .services.alert_manager import alert_manager

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

# Initialize Celery
celery_app = Celery(
    'tasks',
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

# Configure Celery periodic tasks
celery_app.conf.beat_schedule = {
    'scrape-news-every-hour': {
        'task': 'scrape_news',
        'schedule': crontab(minute=0)  # Run every hour
    },
    'analyze-sentiment-every-15-minutes': {
        'task': 'analyze_sentiment',
        'schedule': crontab(minute='*/15')  # Run every 15 minutes
    },
    'process-alerts-every-5-minutes': {
        'task': 'process_alerts',
        'schedule': crontab(minute='*/5')  # Run every 5 minutes
    }
}

# Celery tasks
@celery_app.task(name='scrape_news')
def scrape_news():
    """Celery task to scrape news articles"""
    import asyncio
    asyncio.run(news_scraper.run_scraper())

@celery_app.task(name='analyze_sentiment')
def analyze_sentiment():
    """Celery task to analyze sentiment of news articles"""
    import asyncio
    asyncio.run(sentiment_analyzer.analyze_articles())

@celery_app.task(name='process_alerts')
def process_alerts():
    """Celery task to process and send alerts"""
    import asyncio
    asyncio.run(alert_manager.process_alerts())

# FastAPI startup and shutdown events
@app.on_event("startup")
async def startup_event():
    await db.connect_to_database()

@app.on_event("shutdown")
async def shutdown_event():
    await db.close_database_connection()

# Import and include API routes
from .api.routes import router as api_router
app.include_router(api_router, prefix="/api")

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Stock Sentiment Analysis API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)