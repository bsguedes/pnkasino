# achievement_user.py

from app import db
from sqlalchemy import func
from flask_login import current_user


class AchievementUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievement.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    achievement = db.relationship("Achievement")

    def as_json(self):
        description = self.achievement.description
        if not current_user.has_achievement(self.achievement_id):
            description = "Obtido em %s" % self.created_at.strftime("%b %y")
        return {
            'hero': self.achievement.hero_name,
            'id': self.achievement.hero_id,
            'description': description,
            'created_at': self.created_at
        }

    @staticmethod
    def give_achievement(user_id, achievement_id):
        achievement_user = AchievementUser(user_id=user_id, achievement_id=achievement_id, created_at=func.now())
        db.session.add(achievement_user)
        db.session.commit()
