from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database settings
    supabase_url: str
    mongodb_db_name: str
    redis_url: str
    
    # API settings
    api_secret_key: str
    environment: str
    
    # Service settings
    news_api_key: str
    sentiment_threshold_positive: float
    sentiment_threshold_negative: float
    
    # Logging
    log_level: str

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()