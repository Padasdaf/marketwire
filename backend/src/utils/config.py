from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Supabase settings
    SUPABASE_KEY: str 
    SUPABASE_URL: str 

    SENTIMENT_THRESHOLD_POSITIVE: float = 0.7
    SENTIMENT_THRESHOLD_NEGATIVE: float = -0.7
    LOG_LEVEL: str = "INFO"
    # celery_broker_url: str = "redis://localhost:6379/0"
    # celery_result_backend: str = "redis://localhost:6379/0"
    ALPHA_VANTAGE_API_KEY: str
    MARKETAUX_API_KEY: str
    FINNHUB_API_KEY: str

    @property
    def sentiment_threshold_positive(self) -> float:
        return self.SENTIMENT_THRESHOLD_POSITIVE
        
    @property
    def sentiment_threshold_negative(self) -> float:
        return self.SENTIMENT_THRESHOLD_NEGATIVE

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()