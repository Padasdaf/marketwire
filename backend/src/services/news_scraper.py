import aiohttp
import asyncio
from datetime import datetime, timedelta
from newspaper import Article
from bs4 import BeautifulSoup
from ..utils.logger import logger
from ..models.schemas import Article as ArticleSchema
from ..utils.config import get_settings
from typing import List, Dict
import json

settings = get_settings()

class NewsScraperService:
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Define news sources and their specific scraping strategies
        self.news_sources = {
            'finance.yahoo.com': self._scrape_yahoo_finance,
            'reuters.com': self._scrape_reuters,
            'marketwatch.com': self._scrape_marketwatch
        }

    async def initialize(self):
        """Initialize aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession(headers=self.headers)

    async def close(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def fetch_company_news(self, company_symbol: str, days_back: int = 7) -> List[ArticleSchema]:
        """
        Fetch news articles for a specific company from multiple sources
        """
        try:
            await self.initialize()
            tasks = []
            for source, scrape_method in self.news_sources.items():
                tasks.append(scrape_method(company_symbol, days_back))
            
            # Gather all results
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and flatten results
            articles = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Error scraping news: {str(result)}")
                else:
                    articles.extend(result)

            # Sort articles by publish date
            articles.sort(key=lambda x: x.publish_date, reverse=True)
            
            return articles

        except Exception as e:
            logger.error(f"Error in fetch_company_news: {str(e)}")
            raise
        finally:
            await self.close()

    async def _scrape_yahoo_finance(self, company_symbol: str, days_back: int) -> List[ArticleSchema]:
        """
        Scrape news from Yahoo Finance
        """
        articles = []
        url = f"https://finance.yahoo.com/quote/{company_symbol}/news"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find news articles
                    news_items = soup.find_all('div', {'class': 'Py(14px)'})
                    
                    for item in news_items:
                        try:
                            link = item.find('a')
                            if link and link.get('href'):
                                article_url = f"https://finance.yahoo.com{link['href']}"
                                article = await self._parse_article(article_url)
                                if article:
                                    articles.append(article)
                        except Exception as e:
                            logger.error(f"Error parsing Yahoo Finance article: {str(e)}")
                            continue
                            
        except Exception as e:
            logger.error(f"Error scraping Yahoo Finance: {str(e)}")
        
        return articles

    async def _scrape_reuters(self, company_symbol: str, days_back: int) -> List[ArticleSchema]:
        """
        Scrape news from Reuters
        """
        articles = []
        url = f"https://www.reuters.com/search/news?blob={company_symbol}"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find news articles
                    news_items = soup.find_all('div', {'class': 'search-result-content'})
                    
                    for item in news_items:
                        try:
                            link = item.find('a')
                            if link and link.get('href'):
                                article_url = f"https://www.reuters.com{link['href']}"
                                article = await self._parse_article(article_url)
                                if article:
                                    articles.append(article)
                        except Exception as e:
                            logger.error(f"Error parsing Reuters article: {str(e)}")
                            continue
                            
        except Exception as e:
            logger.error(f"Error scraping Reuters: {str(e)}")
        
        return articles

    async def _parse_article(self, url: str) -> ArticleSchema:
        """
        Parse article content using newspaper3k
        """
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            return ArticleSchema(
                url=url,
                title=article.title,
                content=article.text,
                publish_date=article.publish_date or datetime.utcnow(),
                source=url.split('/')[2],
                company_symbol=None,  # Will be filled by the caller
                sentiment_score=None,
                sentiment_label=None
            )
        except Exception as e:
            logger.error(f"Error parsing article {url}: {str(e)}")
            return None

    def _clean_text(self, text: str) -> str:
        """
        Clean article text by removing extra whitespace and special characters
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = " ".join(text.split())
        # Remove special characters
        text = text.replace('\n', ' ').replace('\r', ' ')
        return text