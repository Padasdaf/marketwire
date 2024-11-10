from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Supabase settings
    supabase_key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im13dGlmYWdoanFibHlrcmhxdHpxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzA3ODU0NzAsImV4cCI6MjA0NjM2MTQ3MH0.9sItFVLjb54T0bSO1QE97NxnF6Ob1vzFwdl1nQT2JsE"
    supabase_url: str = "https://mwtifaghjqblykrhqtzq.supabase.co"
    
    # # Celery settings
    # celery_broker_url: str = "redis://localhost:6379/0"
    # celery_result_backend: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()