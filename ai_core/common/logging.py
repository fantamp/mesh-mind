import sys
from loguru import logger
from ai_core.common.config import settings

def setup_logging():
    """
    Configures logging using loguru.
    """
    logger.remove()  # Remove default handler
    
    logger.add(
        sys.stderr,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # Optional: Add file logging if needed in the future
    # logger.add(f"logs/mesh_mind.log", rotation="10 MB", level=settings.LOG_LEVEL)

    logger.info(f"Logging initialized. Level: {settings.LOG_LEVEL}")

def get_logger(name: str):
    """
    Возвращает logger с указанным именем.
    
    Args:
        name: Имя модуля
        
    Returns:
        Logger instance
    """
    return logger.bind(name=name)
