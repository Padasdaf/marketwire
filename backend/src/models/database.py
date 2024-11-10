from supabase import create_client, Client
from src.utils.config import get_settings
from src.utils.logger import logger
from fastapi import HTTPException
import json
from typing import Optional, List, Dict, Any
from datetime import datetime,timedelta

settings = get_settings()

class Database:
    def __init__(self):
        self.client: Client = None
        self.connect_to_database()
    
    def connect_to_database(self):
        """Initialize Supabase client"""
        logger.info("Connecting to Supabase...")
        try:
            if not self.client:
                self.client = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_KEY
                )
                test_query = self.client.table('companies').select("count").execute()
                logger.info(f"Connection test result: {json.dumps(test_query.data)}")
                logger.info("Connected to Supabase!")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")
        
    def ensure_connection(self):
        """Ensure database connection exists"""
        if not self.client:
            self.connect_to_database()
        return self.client
    
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
    def get_companies(self) ->  List[Dict[str, Any]]:
        """Get all companies"""
        try:
            if not self.client:
                self.connect_to_database()
            logger.info("Executing companies query...")

            response = self.client.table('companies').select("*").execute()
            logger.info(f"Supabase Response: {json.dumps(response.data)}")

            if hasattr(response, 'error') and response.error:
                logger.error(f"Supabase error: {response.error}")
                return []
            
            if not response.data:
                logger.warning("No companies found in the database")
                return []
            
            logger.info(f"Successfully retrieved {len(response.data)} companies")
            return response.data
        except Exception as e:
            logger.error(f"Error fetching companies: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error details: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error fetching companies: {str(e)}")

    def get_company(self, symbol: str):
        """Get company by symbol"""
        try:
            if not self.client:
                self.connect_to_database()
            response = self.client.table('companies')\
                .select("*")\
                .eq('symbol', symbol.upper())\
                .execute()
            
            if not response.data:
                logger.warning(f"No company found with symbol {symbol}")
                return None
            return response.data[0]
        except Exception as e:
            logger.error(f"Error fetching company {symbol}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error fetching company: {str(e)}")
    
    # Article operations
    async def create_article(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new article"""
        try:
            if not self.client:
                await self.connect_to_database()

            if isinstance(article_data.get('publish_date'), datetime):
                article_data['publish_date'] = article_data['publish_date'].isoformat()
            if isinstance(article_data.get('created_at'), datetime):
                article_data['created_at'] = article_data['created_at'].isoformat()
                
            response = self.client.table('news_articles').insert(article_data).execute()
            
            if not response.data:
                raise HTTPException(status_code=500, detail="Failed to create article")
            return response.data[0]
          
        except Exception as e:
            logger.error(f"Error creating article: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error creating article: {str(e)}")

    def store_article(self, article_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Store article in the database"""
        try:
            if not article_data or not isinstance(article_data, dict):
                logger.error("Invalid article data provided")
                return None

            # Convert datetime objects to ISO format strings
            if isinstance(article_data.get('publish_date'), datetime):
                article_data['publish_date'] = article_data['publish_date'].isoformat()
            if isinstance(article_data.get('created_at'), datetime):
                article_data['created_at'] = article_data['created_at'].isoformat()

            # Insert article into database
            response = self.client.table('articles').insert(article_data).execute()
            
            if response.data:
                logger.info(f"Successfully stored article: {article_data.get('title', 'No title')}")
                return response.data[0]
            else:
                logger.error(f"No data returned when storing article: {article_data}")
                return None

        except Exception as e:
            logger.error(f"Error storing article: {str(e)}")
            return None

    def get_company_articles(self, company_symbol: str, days_back: int = 7) -> List[Dict[str, Any]]:
        """Get articles for a company within the specified time period"""
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=days_back)).isoformat()
            
            response = self.client.table('articles')\
                .select('*')\
                .eq('company_symbol', company_symbol.upper())\
                .gte('publish_date', cutoff_date)\
                .order('publish_date', desc=True)\
                .execute()
                
            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error retrieving articles: {str(e)}")
            return []
        
    # Alert operations
    async def create_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new alert"""
        try:
            if not self.client:
                self.connect_to_database()
                
            response = self.client.table('alerts').insert(alert_data).execute()
            
            if not response.data:
                raise HTTPException(status_code=500, detail="Failed to create alert")
                
            return response.data[0]
        except Exception as e:
            logger.error(f"Error creating alert: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error creating alert: {str(e)}")


    async def get_user_alerts(self, user_id: str) -> List[Dict[str, Any]]:
        """Get alerts for a user"""
        try:
            if not self.client:
                self.connect_to_database()
                
            response = self.client.table('alerts')\
                .select("*")\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .execute()
                
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching alerts for user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error fetching alerts: {str(e)}")


# Create a database instance
db = Database()