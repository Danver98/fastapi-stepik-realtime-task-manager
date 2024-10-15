import logging
import sys
from fastapi import Request

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# StreamHandler for console output
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

async def logging_middleware(request: Request, call_next):
    """Logging middleware"""
    logger.info("=======logging info=======")
    logger.info(f"Request: {request.method} {request.url}")
    logger.info("=======logging info=======")
    response = await call_next(request)
    logger.info("=======logging info=======")
    logger.info(f"Response: {response.status_code}")
    logger.info("=======logging info=======")
    return response
