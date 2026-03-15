import time, logging
from app import create_app
from database.db import init_db
from scanner.scheduler import start_scheduler

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s")

if __name__ == "__main__":
    app = create_app()
    init_db(app)
    start_scheduler(app)
    logging.getLogger(__name__).info("Worker running...")
    while True:
        time.sleep(60)
