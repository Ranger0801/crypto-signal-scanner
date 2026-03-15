import logging
from flask import Flask, render_template
from flask_cors import CORS
from config import Config
from database.db import db, init_db
from api.routes import api_bp

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s")

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)
    db.init_app(app)
    app.register_blueprint(api_bp)

    @app.route("/")
    def index(): return render_template("index.html")

    @app.route("/scanner")
    def scanner(): return render_template("scanner.html")

    @app.route("/coin/<symbol>")
    def coin_page(symbol): return render_template("coin.html", symbol=symbol.upper())

    return app

if __name__ == "__main__":
    app = create_app()
    init_db(app)
    from scanner.scheduler import start_scheduler
    start_scheduler(app)
    app.run(host="0.0.0.0", port=5000, debug=Config.DEBUG, use_reloader=False)
