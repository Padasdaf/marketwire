from supabase import create_client, Client
from src.utils.config import get_settings
from src.utils.logger import logger

settings = get_settings()

class Database:
    client: Client = None
    
    async def connect_to_database(self):
        """Initialize Supabase client"""
        logger.info("Connecting to Supabase...")
        self.client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        logger.info("Connected to Supabase!")
    
    async def close_database_connection(self):
        """Clean up any resources"""
        logger.info("Cleaning up Supabase connection...")
        self.client = None
        logger.info("Supabase connection cleaned up!")
    
    # User operations
    # async def create_user(self, email: str, password: str, username: str):
        """Create a new user"""
        try:
            auth_response = await self.client.auth.sign_up({
                "email": email,
                "password": password
            })
            
            # Create user profile in users table
            user_data = {
                "id": auth_response.user.id,
                "email": email,
                "username": username,
                "created_at": "now()"
            }
            
            return await self.client.table('users').insert(user_data).execute()
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise
    
    # Company operations
    async def get_companies(self):
        """Get all companies"""
        try:
            response = await self.client.table('companies').select("*").execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching companies: {str(e)}")
            raise

    async def get_company(self, symbol: str):
        """Get company by symbol"""
        try:
            response = await self.client.table('companies')\
                .select("*")\
                .eq('symbol', symbol)\
                .single()\
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching company {symbol}: {str(e)}")
            raise
    
    # Article operations
    async def create_article(self, article_data: dict):
        """Create a new article"""
        try:
            return await self.client.table('articles').insert(article_data).execute()
        except Exception as e:
            logger.error(f"Error creating article: {str(e)}")
            raise

    async def get_company_articles(self, company_symbol: str, limit: int = 10):
        """Get recent articles for a company"""
        try:
            response = await self.client.table('articles')\
                .select("*")\
                .eq('company_symbol', company_symbol)\
                .order('publish_date', desc=True)\
                .limit(limit)\
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching articles for {company_symbol}: {str(e)}")
            raise
    
    # Alert operations
    async def create_alert(self, alert_data: dict):
        """Create a new alert"""
        try:
            return await self.client.table('alerts').insert(alert_data).execute()
        except Exception as e:
            logger.error(f"Error creating alert: {str(e)}")
            raise

    async def get_user_alerts(self, user_id: str):
        """Get alerts for a user"""
        try:
            response = await self.client.table('alerts')\
                .select("*")\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching alerts for user {user_id}: {str(e)}")
            raise

# Create a database instance
db = Database()