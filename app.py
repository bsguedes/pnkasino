# init.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO

import os


def create_app():
    _app = Flask(__name__)

    _app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
    _app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']

    db.init_app(_app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(_app)

    from models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from auth import auth as auth_blueprint
    _app.register_blueprint(auth_blueprint)
    from main import main as main_blueprint
    _app.register_blueprint(main_blueprint)
    from admin import admin as admin_blueprint
    _app.register_blueprint(admin_blueprint)
    from fantasy import fantasy as fantasy_blueprint
    _app.register_blueprint(fantasy_blueprint)
    from roulette import roulette as roulette_blueprint
    _app.register_blueprint(roulette_blueprint)
    from book import book as book_blueprint
    _app.register_blueprint(book_blueprint)
    from prfl import prfl as profile_blueprint
    _app.register_blueprint(profile_blueprint)

    socket_io.init_app(_app)

    from roulette import start_roulette
    start_roulette()

    return _app


db = SQLAlchemy()
socket_io = SocketIO()


if __name__ == '__main__':
    app = create_app()
    app.run()
else:
    app = create_app()
