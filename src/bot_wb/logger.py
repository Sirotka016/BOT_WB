from loguru import logger
import sys


logger.remove()
logger.add(
    sys.stdout,
    level="INFO",
    enqueue=True,
    backtrace=False,
    diagnose=False,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
           "<level>{level: <7}</level> | "
           "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
           "<level>{message}</level>",
)
