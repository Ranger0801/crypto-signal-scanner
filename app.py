from flask import Flask, render_template, jsonify
from flask_cors import CORS
from config import DEBUG, SECRET_KEY
from database.db import init_db
from api.routes import api_bp
from scanner.scheduler import start_scheduler

app = Flask(__name__)
app.secret_key = SECRET_KEY
CORS(app)
app.register_blueprint(api_bp)

@app.route("/")
def index(): return render_template("index.html")

@app.route("/health")
def health(): return jsonify({"status": "ok"})

@app.errorhandler(404)
def not_found(e): return render_template("index.html")

if __name__ == "__main__":
    init_db()
    scheduler = start_scheduler()
    try:
        app.run(debug=DEBUG, use_reloader=False, host="0.0.0.0", port=5000)
    finally:
        scheduler.shutdown()
