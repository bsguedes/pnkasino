# models.py

from flask_login import UserMixin
from app import db


class League(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    name = db.Column(db.String(200))
    categories = db.relationship('Category', lazy=True, foreign_keys="Category.league_id")


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    pnkoins = db.Column(db.Integer)
    bets = db.relationship('Bet', backref='user', lazy=True)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    question = db.Column(db.String(200))
    max_bet = db.Column(db.Integer)
    state = db.Column(db.String(20))
    options = db.relationship('Option', lazy=True, foreign_keys="Option.category_id")
    bets = db.relationship('Bet', lazy=True, foreign_keys="Bet.category_id")
    winner_option_id = db.Column(db.Integer, db.ForeignKey('option.id'), nullable=True)
    league_id = db.Column(db.Integer, db.ForeignKey('league.id'), nullable=False)
    league = db.relationship("League", back_populates="categories")


class Option(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    name = db.Column(db.String(200))
    odds = db.Column(db.Float)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    bets = db.relationship('Bet', lazy=True, foreign_keys="Bet.option_id")


class Bet(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    option_id = db.Column(db.Integer, db.ForeignKey('option.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    value = db.Column(db.Integer)
    category = db.relationship("Category", back_populates="bets")
    option = db.relationship("Option", back_populates="bets")

    def result(self):
        if self.category.state == 'available':
            return 'Waiting'
        else:
            return 'TODO'
