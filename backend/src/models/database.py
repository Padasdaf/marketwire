from motor.motor_asyncio import AsyncIOMotorClient
from ..utils.config import get_settings
from ..utils.logger import logger

settings = get_settings()

class Database:
    client: AsyncIOMotorClient = None
    
    async def connect_to_database(self):
        logger.info("Connecting to MongoDB...")
        self.client = AsyncIOMotorClient(settings.mongodb_url)
        logger.info("Connected to MongoDB!")
    
    async def close_database_connection(self):
        logger.info("Closing MongoDB connection...")
        if self.client is not None:
            self.client.close()
            logger.info("MongoDB connection closed!")
    
    @property
    def db(self):
        return self.client[settings.mongodb_db_name]

# Create a database instance
db = Database()
