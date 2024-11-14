import httpx
import asyncio
from bs4 import BeautifulSoup
from newspaper import Article
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from src.utils.logger import logger
from src.models.schemas import Article as ArticleSchema
from src.utils.config import get_settings
import json
from src.services.rate_limiter import RateLimiter, rate_limited
from src.services.sentiment_analyzer import sentiment_analyzer, SentimentAnalyzer
import aiohttp
from src.services.supabase_client_service import supabase

settings = get_settings()

class NewsScraperService:
    def __init__(self):
        self.session = None
        self.rate_limiter = RateLimiter(max_concurrent=5)
        self.cache = {}
        self.sentiment_analyzer = SentimentAnalyzer()
        
        # Define headers for each service
        self.headers = {
            'alpha_vantage': {
                'User-Agent': 'Stock Sentiment Analysis/1.0',
                'Accept': 'application/json'
            },
            'marketaux': {
                'User-Agent': 'Stock Sentiment Analysis/1.0',
                'Accept': 'application/json',
                'Authorization': f'Bearer {settings.MARKETAUX_API_KEY}'
            },
            'finnhub': {
                'User-Agent': 'Stock Sentiment Analysis/1.0',
                'Accept': 'application/json',
                'X-Finnhub-Token': settings.FINNHUB_API_KEY
            },
            'yahoo_finance': {
                'User-Agent': 'Mozilla/5.0',
                'Accept': 'application/json'
            }
        }

        # Define news sources
        self.news_sources = {
            'alpha_vantage': {
                'base_url': 'https://www.alphavantage.co/query',
                'params': lambda symbol: {
                    'function': 'NEWS_SENTIMENT',
                    'tickers': symbol,
                    'apikey': settings.ALPHA_VANTAGE_API_KEY
                }
            },
            'marketaux': {
                'base_url': 'https://api.marketaux.com/v1/news/all',
                'params': lambda symbol: {
                    'symbols': symbol,
                    'api_token': settings.MARKETAUX_API_KEY
                }
            },
            'finnhub': {
                'base_url': 'https://finnhub.io/api/v1/company-news',
                'params': lambda symbol: {
                    'symbol': symbol,
                    'from': (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d'),
                    'to': datetime.utcnow().strftime('%Y-%m-%d'),
                    'token': settings.FINNHUB_API_KEY
                }
            },
            'yahoo_finance': {
                'base_url': 'https://query2.finance.yahoo.com/v1/finance/search',
                'params': lambda symbol: {
                    'q': symbol,
                    'newsCount': '20'
                }
            }
        }

    async def initialize(self):
        """Initialize the scraper with database connection and session"""
        try:
            # Initialize database connection
            self.db = supabase
            
            # Initialize HTTP session with proper headers
            default_headers = {
                'User-Agent': 'Stock Sentiment Analysis/1.0',
                'Accept': 'application/json'
            }
            
            self.session = httpx.AsyncClient(
                timeout=30.0,
                headers=default_headers,
                follow_redirects=True
            )
            
            logger.info("NewsScraperService initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing NewsScraperService: {str(e)}")
            raise e

    @rate_limited
    async def _fetch_article_content_with_retry(self, url: str, max_retries: int = 3) -> Optional[str]:
        """Improved article content fetching using httpx"""
        if not url:
            return None

        for attempt in range(max_retries):
            try:
                response = await self.session.get(url)
                if response.status_code == 200:
                    html = response.text
                    
                    # Try using newspaper3k first
                    try:
                        article = Article(url)
                        article.download_state = 2
                        article.html = html
                        article.parse()
                        content = article.text
                        if content and len(content.strip()) >= 50:
                            return content[:self.max_content_length]
                    except Exception as e:
                        logger.debug(f"newspaper3k parsing failed: {str(e)}")

                    # Fall back to BeautifulSoup
                    try:
                        soup = BeautifulSoup(html, 'html.parser')
                        paragraphs = soup.find_all('p')
                        content = ' '.join([p.get_text(strip=True) for p in paragraphs])
                        if content and len(content.strip()) >= 50:
                            return content[:self.max_content_length]
                    except Exception as e:
                        logger.debug(f"BeautifulSoup parsing failed: {str(e)}")

                elif response.status_code in [429, 503, 502, 404]:
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                    continue

            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                continue

        return None

    async def close(self):
        """Close httpx session"""
        if self.session:
            await self.session.aclose()
            self.session = None

    def _get_cached_news(self, company_symbol: str, days_back: int) -> Optional[List[ArticleSchema]]:
        """Get cached news if available and fresh"""
        cache_key = f"{company_symbol}_{days_back}"
        if cache_key in self.cache:
            cache_time, cached_data = self.cache[cache_key]
            if datetime.now() - cache_time < timedelta(hours=1):  # Cache for 1 hour
                return cached_data
        return None

    def _cache_news(self, company_symbol: str, days_back: int, articles: List[ArticleSchema]):
        """Cache news articles"""
        cache_key = f"{company_symbol}_{days_back}"
        self.cache[cache_key] = (datetime.now(), articles)

    async def fetch_company_news(self, company_symbol: str, days_back: int = 7) -> List[ArticleSchema]:
        """Fetch news from multiple sources with detailed logging"""
        try:
            cached_news = self._get_cached_news(company_symbol, days_back)
            if cached_news:
                logger.info("Returning cached news")
                return cached_news

            await self.initialize()
            all_articles = []
            
            # Create aiohttp session if not exists
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            logger.info(f"Fetching news for {company_symbol} from multiple sources")
            
            # Fetch from all sources concurrently
            tasks = []
            for source_name, source_config in self.news_sources.items():
                logger.info(f"Creating task for {source_name}")
                url = source_config['base_url']
                params = source_config['params'](company_symbol)
                headers = self.headers.get(source_name, self.headers['yahoo_finance'])
                
                logger.info(f"{source_name} request details:")
                logger.info(f"URL: {url}")
                logger.info(f"Params: {params}")
                logger.info(f"Headers: {headers}")
                
                task = asyncio.create_task(self._fetch_from_source(
                    source_name,
                    source_config,
                    company_symbol,
                    days_back
                ))
                tasks.append(task)
            
            # Wait for all sources
            logger.info(f"Waiting for {len(tasks)} tasks to complete")
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results with better error handling
            for idx, source_articles in enumerate(results):
                source_name = list(self.news_sources.keys())[idx]
                if isinstance(source_articles, Exception):
                    logger.error(f"Error from {source_name}: {str(source_articles)}")
                    continue
                elif isinstance(source_articles, list):
                    logger.info(f"Got {len(source_articles)} articles from {source_name}")
                    all_articles.extend(source_articles)
                else:
                    logger.warning(f"Unexpected result type from {source_name}: {type(source_articles)}")
            
            # Sort by date and limit to most recent
            all_articles.sort(key=lambda x: x.publish_date, reverse=True)
            all_articles = all_articles[:20]  # Limit to 20 most recent articles
            
            logger.info(f"Total articles collected: {len(all_articles)}")
            
            if all_articles:
                self._cache_news(company_symbol, days_back, all_articles)
            
            return all_articles

        except Exception as e:
            logger.error(f"Error in fetch_company_news: {str(e)}")
            return []
        finally:
            await self.close()

    async def _fetch_from_source(self, source_name: str, source_config: Dict, company_symbol: str, days_back: int) -> List[ArticleSchema]:
        """Fetch news from a specific source with detailed logging"""
        try:
            if not self.session:
                await self.initialize()

            params = source_config['params'](company_symbol)
            url = source_config['base_url']
            
            # Get source-specific headers
            headers = self.headers.get(source_name, {}).copy()
            
            logger.info(f"=== Fetching from {source_name} ===")
            logger.info(f"URL: {url}")
            logger.info(f"Params: {params}")
            logger.info(f"Headers: {headers}")

            response = await self.session.get(
                url,
                params=params,
                headers=headers,
                follow_redirects=True
            )
            
            logger.info(f"{source_name} status code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    logger.info(f"{source_name} response received. First 200 chars: {str(data)[:200]}")
                    
                    if source_name == 'alpha_vantage':
                        return await self._process_alpha_vantage(data, company_symbol)
                    elif source_name == 'marketaux':
                        return await self._process_marketaux(data, company_symbol)
                    elif source_name == 'finnhub':
                        return await self._process_finnhub(data, company_symbol)
                    elif source_name == 'yahoo_finance':
                        return await self._process_yahoo_finance(data, company_symbol)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON from {source_name}: {str(e)}")
                    logger.error(f"Raw response: {response.text[:200]}")
            else:
                logger.error(f"Error response from {source_name}: Status {response.status_code}")
                logger.error(f"Error details: {response.text[:200]}")
        
            return []

        except Exception as e:
            logger.error(f"Exception while fetching from {source_name}: {str(e)}")
            logger.exception(e)
            return []

    # Add processing methods for each source
    async def _process_yahoo_finance(self, data: Dict, company_symbol: str, days_back: int) -> List[ArticleSchema]:
        """Process Yahoo Finance response"""
        # Existing Yahoo Finance processing code...

    async def _process_alpha_vantage(self, data: Dict, company_symbol: str) -> List[ArticleSchema]:
        """Process Alpha Vantage response"""
        articles = []
        try:
            feed_data = data.get('feed', [])
            logger.info(f"Processing {len(feed_data)} articles from Alpha Vantage")
            
            for item in feed_data:
                try:
                    # Convert timestamp to datetime
                    publish_date = datetime.strptime(
                        item.get('time_published', ''), 
                        '%Y%m%dT%H%M%S'
                    )
                    
                    article = ArticleSchema(
                        url=item.get('url', ''),
                        title=item.get('title', ''),
                        content=item.get('summary', ''),
                        publish_date=publish_date,
                        source='Alpha Vantage',
                        company_symbol=company_symbol,
                        sentiment_score=float(item.get('overall_sentiment_score', 0)),
                        sentiment_label=item.get('overall_sentiment_label', 'neutral')
                    )
                    articles.append(article)
                except Exception as e:
                    logger.error(f"Error processing Alpha Vantage article: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in Alpha Vantage processing: {str(e)}")
        return articles

    async def _process_marketaux(self, data: Dict, company_symbol: str) -> List[ArticleSchema]:
        """Process Marketaux response"""
        articles = []
        try:
            news_data = data.get('data', [])
            logger.info(f"Processing {len(news_data)} articles from Marketaux")
            
            for item in news_data:
                try:
                    publish_date = datetime.strptime(
                        item.get('published_at', ''), 
                        '%Y-%m-%dT%H:%M:%S.%fZ'
                    )
                    
                    content = item.get('description', '')
                    
                    # Unpack the tuple returned by analyze_text
                    sentiment_label, sentiment_score = sentiment_analyzer.analyze_text(content)
                    
                    article = ArticleSchema(
                        url=item.get('url', ''),
                        title=item.get('title', ''),
                        content=content,
                        publish_date=publish_date,
                        source=item.get('source', 'Marketaux'),
                        company_symbol=company_symbol,
                        sentiment_score=float(sentiment_score),  # Convert score to float
                        sentiment_label=str(sentiment_label)     # Convert label to string
                    )
                    articles.append(article)
                    logger.info(f"Processed article with sentiment: {sentiment_score}, {sentiment_label}")
                except Exception as e:
                    logger.error(f"Error processing Marketaux article: {str(e)}")
                    continue
        except Exception as e:
            logger.error(f"Error in Marketaux processing: {str(e)}")
        return articles

    async def _process_finnhub(self, data: List, company_symbol: str) -> List[ArticleSchema]:
        """Process Finnhub response"""
        articles = []
        for item in data:
            try:
                publish_date = datetime.fromtimestamp(item.get('datetime', 0))
                content = item.get('summary', '')
                
                # Ensure we have content to analyze
                if not content:
                    content = item.get('headline', '') or item.get('title', '')
                
                # Use analyze_text instead of analyze
                sentiment_label, sentiment_score = self.sentiment_analyzer.analyze_text(content)
                
                article = ArticleSchema(
                    url=item.get('url', ''),
                    title=item.get('headline', '') or item.get('title', ''),
                    content=content,
                    publish_date=publish_date,
                    source=item.get('source', 'Finnhub'),
                    company_symbol=company_symbol,
                    sentiment_score=float(sentiment_score) if sentiment_score is not None else None,
                    sentiment_label=str(sentiment_label) if sentiment_label is not None else None
                )
                articles.append(article)
            except Exception as e:
                logger.error(f"Error processing Finnhub article: {str(e)}")
                continue
        return articles