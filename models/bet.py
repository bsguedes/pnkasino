# bet.py

from app import db


class Bet(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    option_id = db.Column(db.Integer, db.ForeignKey('option.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    value = db.Column(db.Integer)
    category = db.relationship("Category", back_populates="bets")
    option = db.relationship("Option", back_populates="bets")

    def correct_winner(self):
        return self.category.winner_option_id == self.option_id

    def result(self):
        if self.category.league.state != 'finished':
            return 'Aguardando...'
        elif self.category.winner_option_id is None:
            return 'Cashback'
        elif self.category.winner_option_id == self.option_id:
            return 'Ganhou %i ₭' % int(self.value * self.option.odds)
        else:
            return 'Perdeu %i ₭' % int(self.value)
