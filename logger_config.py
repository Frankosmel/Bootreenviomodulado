import logging

def setup_logging():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )
    # Reducir ruido de APScheduler
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
