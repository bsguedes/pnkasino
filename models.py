# models.py

from flask_login import UserMixin
from app import db

SILVER_PERKS = {
    1: '1 ponto a cada ~3300 last hits',
    2: '1 ponto a cada 200 kills',
    3: '1 ponto a cada 500k de dano sofrido',
    4: '1 ponto a cada 1000 segundos de stun',
    5: '1 ponto a cada 100 wards removidas'
}

GOLD_PERKS = {
    1: '1 ponto a cada ~1,4 ultra kills e rampages',
    2: '1 ponto a cada 2 sequencias de 10+ kills',
    3: '1 ponto a cada 200 assists',
    4: '1 ponto a cada ~3,3 couriers mortos',
    5: '1 ponto a cada ~33 creeps stackadas'
}


class League(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    name = db.Column(db.String(200))
    state = db.Column(db.String(20), nullable=False)
    categories = db.relationship('Category', lazy=True, foreign_keys="Category.league_id")
    credit = db.Column(db.Integer, default=0, nullable=False)

    def ranking(self):
        if self.state == 'finished':
            users = {}
            for category in self.categories:
                opt = category.winner_option()
                for bet in category.bets:
                    user_name = bet.user.name
                    if user_name not in users:
                        users[user_name] = {
                            'coins': 0,
                            'hits': 0,
                            'misses': 0
                        }
                    result = 0 if opt is None else -bet.value if bet.option_id != opt.id else int(bet.value * opt.odds)
                    users[user_name]['coins'] += result
                    if result > 0:
                        users[user_name]['hits'] += 1
                    elif result < 0:
                        users[user_name]['misses'] += 1
            return [
                {
                    'position': i + 1,
                    'name': name,
                    'coins': users[name]['coins'],
                    'hits': users[name]['hits'],
                    'misses': users[name]['misses']
                } for i, name in zip(range(len(users)),
                                     sorted([n for n, _ in users.items()], key=lambda e: -users[e]['coins']))]
        else:
            return None


class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    name = db.Column(db.String(50))
    position = db.Column(db.Integer)
    old_base_value = db.Column(db.Integer)
    new_base_value = db.Column(db.Integer)
    current_delta = db.Column(db.Integer)

    def sell_value(self, user):
        extra = 0
        if user.silver_card == self.position:
            extra += self.silver_cost()
        if user.gold_card == self.position:
            extra += self.gold_cost()
        return Card.card_value(self.new_base_value + extra, self.current_delta - 2)

    def value(self):
        return Card.card_value(self.new_base_value, self.current_delta)

    def current_value(self, user):
        extra = 0
        if user.silver_card == self.position:
            extra += self.silver_cost()
        if user.gold_card == self.position:
            extra += self.gold_cost()
        return Card.card_value(self.new_base_value + extra, self.current_delta)

    def silver_cost(self):
        return int(((self.value()/10) ** 2)/1000) * 10

    def gold_cost(self):
        return int(((self.value()/10) ** 2)/500) * 10

    def silver_perk(self):
        return SILVER_PERKS[self.position]

    def gold_perk(self):
        return GOLD_PERKS[self.position]

    def color(self, silver, gold):
        if self.position == silver:
            return 'has-background-grey-light'
        if self.position == gold:
            return 'has-background-warning'
        return 'is-info'

    @staticmethod
    def card_value(base, delta):
        return int((base * (1 + delta * 2 / 100)) // 10 * 10)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000), nullable=False)
    rec_key = db.Column(db.String(1000), nullable=True)
    pnkoins = db.Column(db.Integer, nullable=False)
    earnings = db.Column(db.Integer, default=0, nullable=False)
    roulette_earnings = db.Column(db.Integer, default=0, nullable=False)
    fantasy_earnings = db.Column(db.Integer, default=0, nullable=False)
    bets = db.relationship('Bet', backref='user', lazy=True)
    last_login = db.Column(db.DateTime)
    is_admin = db.Column(db.Integer, default=0)
    card_1_id = db.Column(db.Integer, db.ForeignKey('card.id'), nullable=True)
    card_2_id = db.Column(db.Integer, db.ForeignKey('card.id'), nullable=True)
    card_3_id = db.Column(db.Integer, db.ForeignKey('card.id'), nullable=True)
    card_4_id = db.Column(db.Integer, db.ForeignKey('card.id'), nullable=True)
    card_5_id = db.Column(db.Integer, db.ForeignKey('card.id'), nullable=True)
    silver_card = db.Column(db.Integer, nullable=True)
    gold_card = db.Column(db.Integer, nullable=True)
    buy_1 = db.Column(db.Integer, nullable=True)
    buy_2 = db.Column(db.Integer, nullable=True)
    buy_3 = db.Column(db.Integer, nullable=True)
    buy_4 = db.Column(db.Integer, nullable=True)
    buy_5 = db.Column(db.Integer, nullable=True)
    stats_name = db.Column(db.String(100), nullable=True)

    def finished_bets_without_cashback(self):
        return sum([b.value for b in self.bets if b.category.league.state == 'finished' and b.correct_winner()])

    def is_admin_user(self):
        return self.is_admin == 1

    def has_team(self):
        v = [self.card_1_id, self.card_2_id, self.card_3_id, self.card_4_id, self.card_5_id]
        return any(x is not None for x in v)

    def worth(self):
        on_hold = sum([b.value for b in self.bets if b.category.league.state in ['available', 'blocked']])
        cards = sum(v['sell_value'] for _, v in self.team().items())
        return self.pnkoins + on_hold + cards

    def team(self):
        team = {}
        positions = ['hard_carry', 'mid', 'offlane', 'support', 'hard_support']
        card_ids = [self.card_1_id, self.card_2_id, self.card_3_id, self.card_4_id, self.card_5_id]
        buy_values = [self.buy_1, self.buy_2, self.buy_3, self.buy_4, self.buy_5]

        for p, c, v in zip(positions, card_ids, buy_values):
            if c is not None:
                card = Card.query.filter_by(id=c).first()
                team[p] = {
                    'card': card.name,
                    'buy_value': v,
                    'sell_value': card.sell_value(self),
                    'points': card.current_value(self) / 500
                }
        return team

    def has_card(self, position):
        return (position == 1 and self.card_1_id is not None) or \
               (position == 2 and self.card_2_id is not None) or \
               (position == 3 and self.card_3_id is not None) or \
               (position == 4 and self.card_4_id is not None) or \
               (position == 5 and self.card_5_id is not None)

    def set_card(self, card):
        if card.position == 1:
            self.card_1_id = card.id
            self.buy_1 = card.value()
        elif card.position == 2:
            self.card_2_id = card.id
            self.buy_2 = card.value()
        elif card.position == 3:
            self.card_3_id = card.id
            self.buy_3 = card.value()
        elif card.position == 4:
            self.card_4_id = card.id
            self.buy_4 = card.value()
        elif card.position == 5:
            self.card_5_id = card.id
            self.buy_5 = card.value()

    def set_additional_buy_cost(self, card, value):
        if card.position == 1:
            self.buy_1 += value
        elif card.position == 2:
            self.buy_2 += value
        elif card.position == 3:
            self.buy_3 += value
        elif card.position == 4:
            self.buy_4 += value
        elif card.position == 5:
            self.buy_5 += value

    def clear_card(self, card):
        if card.position == 1:
            self.card_1_id = None
            self.buy_1 = None
        elif card.position == 2:
            self.card_2_id = None
            self.buy_2 = None
        elif card.position == 3:
            self.card_3_id = None
            self.buy_3 = None
        elif card.position == 4:
            self.card_4_id = None
            self.buy_4 = None
        elif card.position == 5:
            self.card_5_id = None
            self.buy_5 = None
        was_promoted = False
        if card.position == self.silver_card:
            self.silver_card = None
            was_promoted = True
        if card.position == self.gold_card:
            self.gold_card = None
            was_promoted = True
        return was_promoted

    def has_player(self, player):
        for i in [self.card_1_id, self.card_2_id, self.card_3_id, self.card_4_id, self.card_5_id]:
            if i is not None:
                c = Card.query.filter_by(id=i).first()
                if c.name == player:
                    return True
        return False


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    question = db.Column(db.String(200))
    max_bet = db.Column(db.Integer)
    options = db.relationship('Option', lazy=True, foreign_keys="Option.category_id")
    bets = db.relationship('Bet', lazy=True, foreign_keys="Bet.category_id")
    winner_option_id = db.Column(db.Integer, db.ForeignKey('option.id'), nullable=True)
    league_id = db.Column(db.Integer, db.ForeignKey('league.id'), nullable=False)
    league = db.relationship("League", back_populates="categories")

    def has_winner(self):
        return self.winner_option_id is not None

    def winner_option(self):
        if self.winner_option_id is None:
            return None
        return Option.query.filter_by(id=self.winner_option_id).first()


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
