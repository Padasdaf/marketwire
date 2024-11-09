from newspaper import Article
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

class NewsScraperService:
    def __init__(self):
        self.news_sources = [
            'reuters.com/business',
            'finance.yahoo.com',
            'bloomberg.com'
        ]
    
    async def fetch_company_news(self, company_symbol: str, days_back: int = 7):
        """
        Fetches news articles for a given company from multiple sources
        """
        articles = []
        
        for source in self.news_sources:
            try:
                # Use API or web scraping depending on source
                raw_articles = await self._fetch_from_source(source, company_symbol)
                articles.extend(raw_articles)
            except Exception as e:
                logger.error(f"Error fetching from {source}: {str(e)}")
        
        return self._process_articles(articles)
    
    def _process_articles(self, articles):
        """
        Cleans and structures the article data
        """
        processed = []
        for article in articles:
            processed.append({
                'title': article.title,
                'text': article.text,
                'date': article.publish_date,
                'source_url': article.url
            })
        return processed