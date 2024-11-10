from supabase import create_client
from src.utils.config import get_settings
from src.utils.logger import logger;

settings = get_settings()

class SupabaseClient:
    def __init__(self):
        self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        
    async def get_user_companies(self, user_id: str) -> list:
        """Get list of companies a user is tracking"""
        try:
            response = await self.client.table('user_company_preferences') \
                .select('company_symbol') \
                .eq('user_id', user_id) \
                .execute()
            return [row['company_symbol'] for row in response.data] or []
        except Exception as e:
            logger.error(f"Error fetching user companies: {str(e)}")
            return []
        
    async def save_article(self, article_data: dict):
        """Save a news article to the database"""
        try:
            await self.client.table('news_articles').insert(article_data).execute()
        except Exception as e:
            logger.error(f"Error saving article data: {str(e)}")
        
    async def save_sentiment_alert(self, alert_data: dict):
        """Save a sentiment alert to the database"""
        return await self.client.table('sentiment_alerts').insert(alert_data).execute()
        
    async def get_unprocessed_articles(self) -> list:
        """Get articles that haven't been analyzed for sentiment"""
        response = await self.client.table('news_articles') \
            .select('*') \
            .eq('sentiment_score', 0.0) \
            .execute()
        return response.data

supabase = SupabaseClient()