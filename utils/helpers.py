import logging
import datetime

def setup_logging(level="info"):
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.FileHandler("stealth_qna.log"), logging.StreamHandler()]
    )

def get_timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")