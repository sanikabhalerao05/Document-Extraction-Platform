import sys
from loguru import logger

def setup_logging():
    # Remove default logger
    logger.remove()

    # Add custom structured logger
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True,
    )

    # Optional: File logger for aspect-based logging (errors, transactions)
    logger.add(
        "logs/app_{time}.log",
        rotation="10 MB",
        retention="7 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message} | {extra}",
    )

    return logger

# Export a configured logger instance
app_logger = setup_logging()
