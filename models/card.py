# card.py

from app import db

SILVER_PERKS = {
    1: '1 ponto a cada 200k tower damage',
    2: '1 ponto a cada 160 kills',
    3: '1 ponto a cada 400k de dano sofrido',
    4: '1 ponto a cada 1000 segundos de stun',
    5: '1 ponto a cada 125 wards removidas'
}

GOLD_PERKS = {
    1: '1 ponto a cada 3 jogos com < 1 morte a cada 15 min',
    2: '1 ponto a cada 500k hero damage',
    3: '1 ponto a cada 12 utility items (*)',
    4: '1 ponto a cada 150 assists',
    5: '1 ponto a cada 15 camps stackados'
}


class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
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
        return Card.card_value(self.new_base_value + extra, self.current_delta - (2 if extra == 0 else 4))

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
