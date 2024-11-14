from transformers import pipeline
from typing import Tuple, List, Dict
import re
from src.utils.logger import logger

class SentimentAnalyzer:
    def __init__(self):
        try:
            self.analyzer = pipeline(
                "sentiment-analysis",
                model="ProsusAI/finbert",
                tokenizer="ProsusAI/finbert",
                device=-1
            )
            
            # Enhanced financial terms dictionary with weights
            self.sentiment_terms = {
                # Strong positive terms (weight: 0.3)
                'surge': 0.3, 'soar': 0.3, 'skyrocket': 0.3, 'breakthrough': 0.3,
                'exceptional': 0.3, 'outperform': 0.3, 'strong buy': 0.3,
                'upgrade': 0.3, 'record high': 0.3,
                
                # Moderate positive terms (weight: 0.2)
                'rise': 0.2, 'gain': 0.2, 'improve': 0.2, 'growth': 0.2,
                'positive': 0.2, 'bullish': 0.2, 'beat': 0.2, 'exceeded': 0.2,
                'higher': 0.2, 'upside': 0.2,
                
                # Weak positive terms (weight: 0.1)
                'up': 0.1, 'better': 0.1, 'good': 0.1, 'increase': 0.1,
                
                # Strong negative terms (weight: -0.3)
                'crash': -0.3, 'plummet': -0.3, 'collapse': -0.3, 'downgrade': -0.3,
                'sell-off': -0.3, 'strong sell': -0.3, 'bankruptcy': -0.3,
                
                # Moderate negative terms (weight: -0.2)
                'fall': -0.2, 'decline': -0.2, 'drop': -0.2, 'bearish': -0.2,
                'negative': -0.2, 'miss': -0.2, 'below': -0.2, 'concern': -0.2,
                'risk': -0.2, 'volatile': -0.2,
                
                # Weak negative terms (weight: -0.1)
                'down': -0.1, 'lower': -0.1, 'weak': -0.1, 'decrease': -0.1
            }
            
        except Exception as e:
            logger.error(f"Error initializing sentiment analyzer: {str(e)}")
            raise

    def analyze_text(self, text: str) -> Tuple[str, float]:
        try:
            if not isinstance(text, str) or len(text.strip()) == 0:
                return ("neutral", 0.0)

            text = text.lower()
            
            # Initial model prediction
            chunks = self._split_text(text, max_length=512)
            model_scores = []
            
            for chunk in chunks:
                try:
                    result = self.analyzer(chunk)[0]
                    score = float(result['score'])
                    if result['label'].lower() == 'negative':
                        score = -score
                    model_scores.append(score)
                except Exception as e:
                    logger.error(f"Error analyzing chunk: {str(e)}")
                    continue

            # Calculate term-based sentiment
            term_score = 0.0
            term_matches = 0
            
            for term, weight in self.sentiment_terms.items():
                count = len(re.findall(r'\b' + re.escape(term) + r'\b', text))
                if count > 0:
                    term_score += weight * count
                    term_matches += count

            # Combine model and term-based sentiment
            if model_scores:
                model_avg = sum(model_scores) / len(model_scores)
            else:
                model_avg = 0.0

            if term_matches > 0:
                term_avg = term_score / term_matches
            else:
                term_avg = 0.0

            # Calculate final score with higher weight on term-based sentiment
            final_score = (0.4 * model_avg + 0.6 * term_avg)
            
            # More aggressive thresholds for classification
            if final_score > 0.1:
                return ("positive", round(final_score, 3))
            elif final_score < -0.1:
                return ("negative", round(final_score, 3))
            else:
                return ("neutral", round(final_score, 3))

        except Exception as e:
            logger.error(f"Error in sentiment analysis: {str(e)}")
            return ("neutral", 0.0)

    def _split_text(self, text: str, max_length: int = 512) -> List[str]:
        """Split text into chunks of maximum length"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0

        for word in words:
            if current_length + len(word.split()) > max_length:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = [word]
                    current_length = len(word.split())
            else:
                current_chunk.append(word)
                current_length += len(word.split())

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

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

# Create a global instance
sentiment_analyzer = SentimentAnalyzer()

# Export the instance
__all__ = ['sentiment_analyzer']