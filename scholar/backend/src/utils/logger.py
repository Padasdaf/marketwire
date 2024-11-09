from loguru import logger
import sys
from .config import get_settings

settings = get_settings()

# Configure logger
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    level=settings.log_level,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
logger.add(
    "logs/file_{time}.log",
    rotation="500 MB",
    retention="10 days",
    level=settings.log_level
)

# Add custom levels for our application
logger.level("SCRAPER", no=15, color="<yellow>")
logger.level("SENTIMENT", no=18, color="<blue>")
logger.level("ALERT", no=25, color="<red>")