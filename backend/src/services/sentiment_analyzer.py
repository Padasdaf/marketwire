from transformers import pipeline
from ..utils.logger import logger
from ..models.schemas import Article, SentimentLabel
from typing import List, Dict
import numpy as np
from datetime import datetime
import torch
from concurrent.futures import ThreadPoolExecutor
from functools import partial

class SentimentAnalyzer:
    def __init__(self):
        # Initialize the FinBERT model for financial sentiment analysis
        logger.info("Initializing FinBERT model...")
        try:
            self.analyzer = pipeline(
                "sentiment-analysis",
                model="ProsusAI/finbert",
                device=0 if torch.cuda.is_available() else -1  # Use GPU if available
            )
            logger.info("FinBERT model initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing FinBERT model: {str(e)}")
            raise

        # Define sentiment mapping
        self.sentiment_mapping = {
            'positive': SentimentLabel.POSITIVE,
            'negative': SentimentLabel.NEGATIVE,
            'neutral': SentimentLabel.NEUTRAL
        }

    async def analyze_articles(self, articles: List[Article]) -> List[Article]:
        """
        Analyze sentiment for a batch of articles
        """
        try:
            logger.info(f"Analyzing sentiment for {len(articles)} articles")
            
            # Process articles in batches to avoid memory issues
            batch_size = 10
            processed_articles = []
            
            for i in range(0, len(articles), batch_size):
                batch = articles[i:i + batch_size]
                # Extract text content for batch
                texts = [self._prepare_text(article.content) for article in batch]
                
                # Perform sentiment analysis
                sentiments = self._analyze_batch(texts)
                
                # Update articles with sentiment scores
                for article, sentiment in zip(batch, sentiments):
                    article.sentiment_score = sentiment['score']
                    article.sentiment_label = self.sentiment_mapping[sentiment['label'].lower()]
                    article.processed_date = datetime.utcnow()
                    processed_articles.append(article)
            
            logger.info("Sentiment analysis completed successfully")
            return processed_articles
            
        except Exception as e:
            logger.error(f"Error in analyze_articles: {str(e)}")
            raise

    def _analyze_batch(self, texts: List[str]) -> List[Dict]:
        """
        Analyze sentiment for a batch of texts
        """
        try:
            # Split long texts into chunks to handle length limitations
            chunked_texts = [self._chunk_text(text) for text in texts]
            results = []
            
            for chunks in chunked_texts:
                if not chunks:
                    results.append({'label': 'neutral', 'score': 0.5})
                    continue
                
                # Analyze each chunk
                chunk_sentiments = self.analyzer(chunks)
                
                # Aggregate chunk sentiments
                if isinstance(chunk_sentiments, list):
                    # Calculate weighted average based on confidence scores
                    scores = [
                        (1 if s['label'] == 'positive' else -1 if s['label'] == 'negative' else 0)
                        * s['score']
                        for s in chunk_sentiments
                    ]
                    weights = [s['score'] for s in chunk_sentiments]
                    avg_score = np.average(scores, weights=weights) if weights else 0
                    
                    # Determine final sentiment
                    if avg_score > 0.1:
                        label = 'positive'
                        score = (avg_score + 1) / 2  # Normalize to 0-1 range
                    elif avg_score < -0.1:
                        label = 'negative'
                        score = (-avg_score + 1) / 2
                    else:
                        label = 'neutral'
                        score = 0.5
                        
                    results.append({'label': label, 'score': float(score)})
                else:
                    results.append(chunk_sentiments)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in _analyze_batch: {str(e)}")
            raise

    def _prepare_text(self, text: str) -> str:
        """
        Prepare text for sentiment analysis
        """
        if not text:
            return ""
        
        # Clean and normalize text
        text = text.replace('\n', ' ').replace('\r', ' ')
        text = ' '.join(text.split())  # Remove extra whitespace
        return text

    def _chunk_text(self, text: str, max_length: int = 512) -> List[str]:
        """
        Split text into chunks that fit within model's maximum length
        """
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + 1  # Add 1 for space
            if current_length + word_length > max_length:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks

    def calculate_aggregate_sentiment(self, articles: List[Article]) -> Dict:
        """
        Calculate aggregate sentiment from multiple articles
        """
        if not articles:
            return {
                'score': 0.5,
                'label': SentimentLabel.NEUTRAL,
                'confidence': 0
            }

        # Calculate weighted scores based on recency and source reliability
        weighted_scores = []
        weights = []
        
        for article in articles:
            weight = self._calculate_article_weight(article)
            score = article.sentiment_score
            if score is not None:
                weighted_scores.append(score * weight)
                weights.append(weight)
        
        if not weighted_scores:
            return {
                'score': 0.5,
                'label': SentimentLabel.NEUTRAL,
                'confidence': 0
            }
        
        # Calculate weighted average
        aggregate_score = np.average(weighted_scores, weights=weights)
        confidence = np.std(weighted_scores)  # Use standard deviation as confidence measure
        
        # Determine sentiment label
        if aggregate_score > 0.6:
            label = SentimentLabel.POSITIVE
        elif aggregate_score < 0.4:
            label = SentimentLabel.NEGATIVE
        else:
            label = SentimentLabel.NEUTRAL
        
        return {
            'score': float(aggregate_score),
            'label': label,
            'confidence': float(confidence)
        }

    def _calculate_article_weight(self, article: Article) -> float:
        """
        Calculate weight for an article based on various factors
        """
        # Base weight
        weight = 1.0
        
        # Adjust weight based on article age
        age_hours = (datetime.utcnow() - article.publish_date).total_seconds() / 3600
        age_factor = 1.0 / (1.0 + age_hours/24)  # Decay factor
        weight *= age_factor
        
        # Adjust weight based on source reliability (can be expanded)
        source_reliability = {
            'reuters.com': 1.0,
            'bloomberg.com': 1.0,
            'wsj.com': 1.0,
            'finance.yahoo.com': 0.8,
            'default': 0.6
        }
        source = article.source.lower()
        reliability = source_reliability.get(source, source_reliability['default'])
        weight *= reliability
        
        return weight