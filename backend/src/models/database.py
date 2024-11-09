import os
from supabase import create_client, Client
from motor.motor_asyncio import AsyncIOMotorClient
from ..utils.config import get_settings
from ..utils.logger import logger

settings = get_settings()

class Database:
    client: Client = None
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    async def connect_to_database(self):
        logger.info("Connecting to Supabase...")
        self.client = create_client(url, key)
        logger.info("Connected to Supabase!")
    
    async def close_database_connection(self):
        logger.info("Closing Supabase connection...")
        if self.client is not None:
            self.client.close()
            logger.info("Supabase connection closed!")
    
    @property
    def db(self):
        return self.client

# Create a database instance
db = Database()
