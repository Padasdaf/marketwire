from loguru import logger
import sys
from src.utils.config import get_settings
import logging

settings = get_settings()

# Configure logger
logger=logging.getLogger(__name__)  # Remove default handler
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),  # Ensure correct attribute reference
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
print(f"Log Level from Settings: {settings.LOG_LEVEL}")
# )
# logger.add(
#     sys.stderr,
#     level=settings.log_level,
#     format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
# # )
# logger.add(
#     "logs/file_{time}.log",
#     rotation="500 MB",
#     retention="10 days",
#     level=settings.log_level
# )

# # Add custom levels for our application
# logger.level("SCRAPER", no=15, color="<yellow>")
# logger.level("SENTIMENT", no=18, color="<blue>")
# logger.level("ALERT", no=25, color="<red>")