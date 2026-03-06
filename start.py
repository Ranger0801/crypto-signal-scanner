"""
Gunicorn entry point for Render.
This file initialises the DB and starts the background scanner
before gunicorn begins serving requests.
"""
from app import app
from database.db import init_db
from scanner.scheduler import start_scheduler

init_db()
start_scheduler()

# 'app' is what gunicorn imports
