from datetime import datetime
import asyncio

class AlertManager:
    def __init__(self, db_connection):
        self.db = db_connection
        self.threshold_positive = 0.7  # Configurable threshold
        self.threshold_negative = 0.3
    
    async def check_alerts(self, company_symbol: str, sentiment_score: float):
        """
        Checks if alerts should be triggered based on sentiment analysis
        """
        current_price = await self._get_current_price(company_symbol)
        historic_sentiment = await self._get_historic_sentiment(company_symbol)
        
        if sentiment_score > self.threshold_positive:
            await self._create_alert(
                company_symbol,
                "SELL",
                f"High positive sentiment detected ({sentiment_score:.2f})"
            )
        elif sentiment_score < self.threshold_negative:
            await self._create_alert(
                company_symbol,
                "BUY",
                f"Low sentiment detected ({sentiment_score:.2f})"
            )