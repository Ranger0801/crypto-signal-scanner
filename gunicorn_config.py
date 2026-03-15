import logging
log = logging.getLogger(__name__)

def on_starting(server):
    """Called when gunicorn starts — initialise DB and scanner."""
    from app import create_app
    from database.db import init_db
    from scanner.scheduler import start_scheduler

    app = create_app()
    init_db(app)
    start_scheduler(app)
    log.info("✅ Database initialised and scanner started.")
