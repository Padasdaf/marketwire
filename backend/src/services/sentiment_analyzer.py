from transformers import pipeline
import numpy as np

class SentimentAnalyzer:
    def __init__(self):
        self.analyzer = pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert"  # Financial domain-specific BERT
        )
    
    async def analyze_articles(self, articles):
        """
        Performs sentiment analysis on a batch of articles
        """
        results = []
        for article in articles:
            sentiment = await self._analyze_text(article['text'])
            results.append({
                'article_id': article['id'],
                'sentiment_score': sentiment['score'],
                'sentiment_label': sentiment['label'],
                'confidence': sentiment['confidence']
            })
        return results
    
    def calculate_aggregate_sentiment(self, sentiments):
        """
        Calculates weighted sentiment score based on article recency and reliability
        """
        weights = [self._calculate_weight(s) for s in sentiments]
        return np.average([s['sentiment_score'] for s in sentiments], weights=weights)