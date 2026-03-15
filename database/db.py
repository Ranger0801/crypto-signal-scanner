from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
        _seed_coins()

def _seed_coins():
    import json, os
    from database.models import Coin
    f = os.path.join(os.path.dirname(__file__), "..", "data", "coin_list.json")
    if not os.path.exists(f):
        return
    with open(f) as fp:
        data = json.load(fp)
    for c in data["coins"]:
        if not Coin.query.filter_by(symbol=c["symbol"]).first():
            db.session.add(Coin(symbol=c["symbol"], name=c["name"]))
    db.session.commit()
