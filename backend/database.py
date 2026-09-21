from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def init_db(app):
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'portfolio.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    from models.portfolio import Portfolio, Holding, Performance
    with app.app_context():
        db.create_all()

    return db
