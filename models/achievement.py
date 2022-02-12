# achievement.py

from app import db

CATEGORIES = {
    1: 'Roleta',
    2: 'Fantasy',
    3: 'Apostas',
    4: 'Social',
    5: 'Diversos'
}


class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    hero_id = db.Column(db.Integer, default=0, nullable=False)
    hero_name = db.Column(db.String(256), nullable=False)
    description = db.Column(db.String(256), nullable=False)
    category = db.Column(db.Integer, nullable=True)
    earners = db.relationship('AchievementUser', lazy=True, foreign_keys="AchievementUser.achievement_id")

    def as_json(self):
        return {
            'id': self.id,
            'hero_id': self.hero_id,
            'hero_name': self.hero_name,
            'description': self.description,
            'category': CATEGORIES[self.category] if self.category is not None else '(undefined)',
            'earned_count': len(self.earners)
        }

    def earners_names(self):
        return [e.user.stats_name for e in self.earners]

    @staticmethod
    def categories():
        return CATEGORIES
