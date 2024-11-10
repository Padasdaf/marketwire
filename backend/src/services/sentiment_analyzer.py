from transformers import pipeline
from src.utils.logger import logger
from datetime import datetime
from typing import Tuple, Optional

class SentimentAnalyzer:
    def __init__(self):
        try:
            self.analyzer = pipeline(
                "sentiment-analysis",
                model="ProsusAI/finbert",
                tokenizer="ProsusAI/finbert",
                timeout=30
            )
        except Exception as e:
            logger.error(f"Error initializing sentiment analyzer: {str(e)}")
            raise

    def analyze_text(self, text: str) -> Tuple[str, float]:
        """
        Analyze the sentiment of a given text with improved error handling.
        Returns: (sentiment_label, sentiment_score)
        """
        try:
            # Input validation
            if not text or not isinstance(text, str):
                logger.warning("Invalid input text provided")
                return ("neutral", 0.0)

            text = text.strip()
            if len(text) == 0:
                logger.warning("Empty text provided")
                return ("neutral", 0.0)

            # Split text into manageable chunks
            chunks = self._split_text(text)
            if not chunks:
                return ("neutral", 0.0)

            # Analyze chunks
            total_score = 0.0
            sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}

            for chunk in chunks:
                try:
                    result = self.analyzer(chunk)[0]
                    label = result['label'].lower()  # Ensure lowercase
                    score = float(result['score'])  # Ensure float type

                    # Validate label
                    if label not in sentiment_counts:
                        logger.warning(f"Unexpected sentiment label: {label}")
                        continue

                    # Map and normalize score
                    normalized_score = self._normalize_score(label, score)
                    total_score += normalized_score
                    sentiment_counts[label] += 1

                except Exception as chunk_error:
                    logger.error(f"Error analyzing chunk: {str(chunk_error)}")
                    continue

            # Calculate final results
            if sum(sentiment_counts.values()) == 0:
                logger.warning("No valid sentiment analysis results")
                return ("neutral", 0.0)

            avg_score = total_score / len(chunks)
            max_sentiment = max(sentiment_counts.items(), key=lambda x: x[1])[0]

            # Ensure return values are properly formatted
            return (max_sentiment, round(avg_score, 3))

        except Exception as e:
            logger.error(f"Error in sentiment analysis: {str(e)}")
            return ("neutral", 0.0)

    def _split_text(self, text: str, max_length: int = 512) -> list:
        """Split text into chunks of maximum token length"""
        try:
            words = text.split()
            if not words:
                return []

            chunks = []
            current_chunk = []
            current_length = 0

            for word in words:
                word_length = len(word.split())
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

        except Exception as e:
            logger.error(f"Error splitting text: {str(e)}")
            return []

    def _normalize_score(self, label: str, score: float) -> float:
        """Normalize sentiment scores"""
        sentiment_map = {
            'positive': 1.0,
            'negative': -1.0,
            'neutral': 0.0
        }
        
        try:
            base_score = sentiment_map.get(label, 0.0)
            normalized = base_score * max(min(score, 1.0), 0.0)  # Clamp between 0 and 1
            return round(normalized, 3)
        except Exception as e:
            logger.error(f"Error normalizing score: {str(e)}")
            return 0.0

# Create a single instance to be used across the application
sentiment_analyzer = SentimentAnalyzer()