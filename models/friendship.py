# message.py

from app import db
from datetime import timedelta

FRIENDSHIP_STATES = ['requested', 'friend']


class Friendship(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    created_at = db.Column(db.DateTime, nullable=False)
    state = db.Column(db.String(100), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    invited_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    friend = db.relationship("User", foreign_keys="Friendship.friend_id")
    invited = db.relationship("User", back_populates="friends", foreign_keys="Friendship.invited_id")

    def as_json(self):
        return {
            'friend_id': self.friend_id,
            'friend_name': self.friend.stats_name,
            'invited_id': self.invited_id,
            'invited_name': self.invited.stats_name,
            'state': self.state,
            'created_at': self.created_at - timedelta(hours=3)
        }
