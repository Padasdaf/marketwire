from transformers import pipeline
from ..database import db
from ..utils.logger import logger
from ..utils.config import get_settings
from datetime import datetime, timedelta

settings = get_settings()

class SentimentAnalyzer:
    def __init__(self):
        # Initialize the sentiment analysis pipeline
        self.analyzer = pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert",  # Financial domain-specific BERT model
            tokenizer="ProsusAI/finbert"
        )
        self.positive_threshold = settings.sentiment_threshold_positive
        self.negative_threshold = settings.sentiment_threshold_negative

    def analyze_text(self, text: str) -> tuple:
        """
        Analyze the sentiment of a given text
        Returns: (sentiment_label, sentiment_score)
        """
        try:
            # Truncate text if it's too long (BERT models typically have a max length)
            max_length = 512
            if len(text.split()) > max_length:
                text = " ".join(text.split()[:max_length])

            # Get sentiment prediction
            result = self.analyzer(text)[0]
            label = result['label']
            score = result['score']

            # Map sentiment labels
            sentiment_map = {
                'positive': 1.0,
                'negative': -1.0,
                'neutral': 0.0
            }

            normalized_score = sentiment_map.get(label, 0.0) * score
            return label, normalized_score

        except Exception as e:
            logger.error(f"Error in sentiment analysis: {str(e)}")
            return "neutral", 0.0

    async def analyze_articles(self):
        """
        Analyze sentiment for all unanalyzed news articles
        """
        try:
            # Get unanalyzed articles (where sentiment_score is 0)
            articles = await db.db.news_articles.find(
                {"sentiment_score": 0.0}
            ).to_list(1000)

            for article in articles:
                # Combine title and content for analysis
                text = f"{article['title']} {article['content']}"
                label, score = self.analyze_text(text)

                # Update article with sentiment analysis
                await db.db.news_articles.update_one(
                    {"_id": article["_id"]},
                    {
                        "$set": {
                            "sentiment_score": score,
                            "sentiment_label": label
                        }
                    }
                )

                # Generate alerts if sentiment score exceeds thresholds
                await self._check_and_generate_alerts(article["company_id"], score)

        except Exception as e:
            logger.error(f"Error in analyze_articles: {str(e)}")

    async def _check_and_generate_alerts(self, company_id: str, sentiment_score: float):
        """
        Generate alerts for users if sentiment score exceeds thresholds
        """
        try:
            # Find users who are tracking this company
            users = await db.db.user_preferences.find(
                {
                    "companies": company_id,
                    "is_active": True
                }
            ).to_list(1000)

            for user in users:
                alert_type = None
                if sentiment_score >= self.positive_threshold:
                    alert_type = "sell"  # High positive sentiment might indicate a good time to sell
                elif sentiment_score <= -self.negative_threshold:
                    alert_type = "buy"   # High negative sentiment might indicate a buying opportunity

                if alert_type:
                    # Create sentiment alert
                    alert = {
                        "company_id": company_id,
                        "user_id": user["user_id"],
                        "sentiment_score": sentiment_score,
                        "alert_type": alert_type,
                        "created_at": datetime.utcnow(),
                        "is_sent": False
                    }
                    await db.db.sentiment_alerts.insert_one(alert)

        except Exception as e:
            logger.error(f"Error in _check_and_generate_alerts: {str(e)}")

# Create analyzer instance
sentiment_analyzer = SentimentAnalyzer()