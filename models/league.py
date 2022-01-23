# league.py

from app import db

next_state = {
    'new': 'available',
    'available': 'blocked',
    'blocked': 'finished',
    'finished': None
}


class League(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    name = db.Column(db.String(200))
    state = db.Column(db.String(20), nullable=False)
    categories = db.relationship('Category', lazy=True, foreign_keys="Category.league_id")
    credit = db.Column(db.Integer, default=0, nullable=False)

    def as_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'state': self.state,
            'credit': self.credit,
            'next_state': next_state[self.state],
            'unset': len([c for c in self.categories if c.winner_option_id is None])
        }

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
                    result = 0 if opt is None else -bet.value if bet.option_id != opt.id\
                        else int(bet.value * opt.odds) - bet.value
                    users[user_name]['coins'] += result
                    users[user_name]['profile_id'] = bet.user.id
                    if result > 0:
                        users[user_name]['hits'] += 1
                    elif result < 0:
                        users[user_name]['misses'] += 1
            return [
                {
                    'position': i + 1,
                    'name': name,
                    'profile_id': users[name]['profile_id'],
                    'coins': users[name]['coins'],
                    'hits': users[name]['hits'],
                    'misses': users[name]['misses']
                } for i, name in zip(range(len(users)),
                                     sorted([n for n, _ in users.items()], key=lambda e: -users[e]['coins']))]
        else:
            return None
