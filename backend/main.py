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
import httpx
from datetime import datetime, timedelta

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
        
        # Verify API keys
        settings = get_settings()
        api_keys = {
            'ALPHA_VANTAGE_API_KEY': settings.ALPHA_VANTAGE_API_KEY,
            'MARKETAUX_API_KEY': settings.MARKETAUX_API_KEY,
            'FINNHUB_API_KEY': settings.FINNHUB_API_KEY
        }
        
        for key_name, key_value in api_keys.items():
            if not key_value:
                logger.warning(f"Missing API key: {key_name}")
            else:
                masked_key = key_value[:4] + '*' * (len(key_value) - 4)
                logger.info(f"Found API key for {key_name}: {masked_key}")
                
    except Exception as e:
        logger.error(f"Error in startup: {str(e)}")
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

@app.get("/api/test-news-sources")
async def test_news_sources():
    """Test endpoint to check each news source"""
    settings = get_settings()
    results = {}
    
    # Test Alpha Vantage
    try:
        logger.info("Testing Alpha Vantage API...")
        url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers=AAPL&apikey={settings.ALPHA_VANTAGE_API_KEY}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            logger.info(f"Alpha Vantage Status: {response.status_code}")
            results['alpha_vantage'] = {
                'status': response.status_code,
                'sample_response': str(response.text)[:200] if response.status_code == 200 else response.text
            }
    except Exception as e:
        logger.error(f"Alpha Vantage Error: {str(e)}")
        results['alpha_vantage'] = {'error': str(e)}

    # Test Marketaux
    try:
        logger.info("Testing Marketaux API...")
        url = f"https://api.marketaux.com/v1/news/all?symbols=AAPL&api_token={settings.MARKETAUX_API_KEY}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            logger.info(f"Marketaux Status: {response.status_code}")
            results['marketaux'] = {
                'status': response.status_code,
                'sample_response': str(response.text)[:200] if response.status_code == 200 else response.text
            }
    except Exception as e:
        logger.error(f"Marketaux Error: {str(e)}")
        results['marketaux'] = {'error': str(e)}

    # Test Finnhub
    try:
        logger.info("Testing Finnhub API...")
        url = f"https://finnhub.io/api/v1/company-news?symbol=AAPL&from=2024-11-07&to=2024-11-14&token={settings.FINNHUB_API_KEY}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            logger.info(f"Finnhub Status: {response.status_code}")
            results['finnhub'] = {
                'status': response.status_code,
                'sample_response': str(response.text)[:200] if response.status_code == 200 else response.text
            }
    except Exception as e:
        logger.error(f"Finnhub Error: {str(e)}")
        results['finnhub'] = {'error': str(e)}

    return results

@app.get("/api/debug/{source}/{symbol}")
async def debug_source(source: str, symbol: str):
    """Debug endpoint to test individual news sources"""
    try:
        scraper = NewsScraperService()
        await scraper.initialize()
        
        if source not in scraper.news_sources:
            return {"error": f"Invalid source. Available sources: {list(scraper.news_sources.keys())}"}
        
        source_config = scraper.news_sources[source]
        logger.info(f"Testing {source} for {symbol}")
        articles = await scraper._fetch_from_source(source, source_config, symbol, 7)
        
        return {
            "source": source,
            "symbol": symbol,
            "article_count": len(articles),
            "articles": articles
        }
    except Exception as e:
        logger.error(f"Error in debug endpoint: {str(e)}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await scraper.close()

@app.get("/api/test-api/{source}/{symbol}")
async def test_api(source: str, symbol: str):
    """Test endpoint to check API connection only"""
    try:
        settings = get_settings()
        
        # Configure the API call based on the source
        if source == 'alpha_vantage':
            url = 'https://www.alphavantage.co/query'
            params = {
                'function': 'NEWS_SENTIMENT',
                'tickers': symbol,
                'apikey': settings.ALPHA_VANTAGE_API_KEY
            }
        elif source == 'marketaux':
            url = 'https://api.marketaux.com/v1/news/all'
            params = {
                'symbols': symbol,
                'api_token': settings.MARKETAUX_API_KEY
            }
        elif source == 'finnhub':
            url = f'https://finnhub.io/api/v1/company-news'
            params = {
                'symbol': symbol,
                'from': (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d'),
                'to': datetime.utcnow().strftime('%Y-%m-%d'),
                'token': settings.FINNHUB_API_KEY
            }
        else:
            return {"error": f"Invalid source. Available sources: alpha_vantage, marketaux, finnhub"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            
            return {
                "source": source,
                "status_code": response.status_code,
                "response": response.json() if response.status_code == 200 else response.text
            }
            
    except Exception as e:
        logger.error(f"Error in test API endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)