import aiohttp
import asyncio
from datetime import datetime, timedelta
from newspaper import Article
from bs4 import BeautifulSoup
from src.utils.logger import logger
from src.models.schemas import Article as ArticleSchema
from src.utils.config import get_settings
from typing import List, Dict, Optional
import json
from src.services.rate_limiter import RateLimiter, rate_limited

settings = get_settings()

class NewsScraperService:
    def __init__(self):
        self.session = None
        self.rate_limiter = RateLimiter(max_concurrent=5)
        self.cache = {}
        self.headers = {
            # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive'
        }
        self.max_content_length = 500000  # 500KB limit

    async def initialize(self):
        """Initialize aiohttp session with optimized settings"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            connector = aiohttp.TCPConnector(
                force_close=True,
                limit=10,
                ttl_dns_cache=300,
                # max_header_size=16384
            )
            self.session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=timeout,
                connector=connector
            )

    async def close(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
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

    @rate_limited
    async def fetch_company_news(self, company_symbol: str, days_back: int = 7) -> List[ArticleSchema]:
        """Fetch news articles for a company with improved error handling and caching"""
        try:
            # Check cache first
            cached_news = self._get_cached_news(company_symbol, days_back)
            if cached_news:
                return cached_news

            await self.initialize()
            
            params = {
                'q': str(company_symbol),
                'newsCount': '10',
                'enableFuzzyQuery': 'false',
                'newsQueryId': 'news_cie_vespa',
            }

            base_url = "https://query1.finance.yahoo.com/v1/finance/search"

            async with self.session.get(base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    news_items = data.get('news', [])
                    
                    articles = []
                    cutoff_date = datetime.utcnow() - timedelta(days=days_back)
                    
                    for item in news_items:
                        try:
                            publish_timestamp = item.get('providerPublishTime')
                            if not publish_timestamp:
                                continue
                                
                            publish_date = datetime.fromtimestamp(publish_timestamp)
                            if publish_date < cutoff_date:
                                continue

                            content = await self._fetch_article_content_with_retry(item.get('link', ''))
                            
                            if not content:
                                continue

                            article = ArticleSchema(
                                url=item.get('link', ''),
                                title=item.get('title', ''),
                                content=content,
                                publish_date=publish_date,
                                source=item.get('publisher', ''),
                                company_symbol=company_symbol,
                                sentiment_score=None,
                                sentiment_label=None
                            )
                            articles.append(article)
                            logger.info(f"Successfully parsed article: {article.title}")
                        except Exception as e:
                            logger.error(f"Error parsing single article: {str(e)}")
                            continue

                    # Cache the results before returning
                    self._cache_news(company_symbol, days_back, articles)
                    return articles
                else:
                    logger.error(f"Failed to fetch news: Status {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Error in fetch_company_news: {str(e)}")
            return []
        finally:
            await self.close()

    @rate_limited
    async def _fetch_article_content_with_retry(self, url: str, max_retries: int = 3) -> Optional[str]:
        """Fetch article content with retry mechanism and better error handling"""
        if not url:
            return None

        for attempt in range(max_retries):
            try:
                # Use a fresh session for each attempt to avoid header issues
                async with aiohttp.ClientSession(headers=self.headers) as temp_session:
                    async with temp_session.get(
                        url,
                        allow_redirects=True,
                        timeout=30,
                        
                    ) as response:
                        if response.status == 200:
                            content_length = int(response.headers.get('content-length', 0))
                            if content_length > self.max_content_length:
                                logger.warning(f"Content too large ({content_length} bytes) for {url}")
                                return None

                            # Read content in chunks
                            chunks = []
                            async for chunk in response.content.iter_chunked(8192):
                                chunks.append(chunk)
                            
                            html = b''.join(chunks).decode('utf-8', errors='ignore')
                            if not html:
                                continue

                            article = Article(url)
                            article.download_state = 2
                            article.html = html
                            article.parse()
                            
                            content = article.text
                            if not content or len(content.strip()) < 50:
                                continue
                                
                            return content[:100000]
                            
                        elif response.status in [429, 503]:
                            wait_time = 2 ** attempt
                            await asyncio.sleep(wait_time)
                            continue
                        
                        else:
                            logger.error(f"Failed to fetch article: Status {response.status} for {url}")
                            return None

            # except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            #     logger.error(f"Network error fetching article (attempt {attempt + 1}): {str(e)}")
            #     if attempt < max_retries - 1:
            #         await asyncio.sleep(2 ** attempt)
            #     continue
            except aiohttp.ClientResponseError as e:
                if "Header value is too long" in str(e):
                    logger.error(f"Header too long error on attempt {attempt + 1}: {url}")
                    continue  # Retry without certain headers or with adjusted logic

            except Exception as e:
                logger.error(f"Unexpected error fetching article: {str(e)}")
                return None

        logger.error(f"Failed to fetch article after {max_retries} attempts: {url}")
        return None