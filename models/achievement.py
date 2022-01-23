# achievement.py

from app import db


class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    hero_id = db.Column(db.Integer, default=0, nullable=False)
    hero_name = db.Column(db.String(256), nullable=False)
    description = db.Column(db.String(256), nullable=False)
    earners = db.relationship('AchievementUser', lazy=True, foreign_keys="AchievementUser.achievement_id")

    def as_json(self):
        return {
            'hero_id': self.hero_id,
            'hero_name': self.hero_name,
            'description': self.description,
            'earned_count': len(self.earners)
        }
