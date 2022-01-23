# message.py

from app import db
from flask_login import current_user
from models.vote import Vote
from datetime import timedelta


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    message = db.Column(db.String(256), nullable=False)
    likes = db.Column(db.Integer, default=0, nullable=False)
    dislikes = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    parent_message_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=True)
    responses = db.relationship('Message', lazy=True, foreign_keys="Message.parent_message_id")

    def as_json(self):
        return {
            'message': self.message,
            'likes': self.likes,
            'dislikes': self.dislikes,
            'can_vote': not current_user.is_anonymous and \
                        Vote.query.filter_by(message_id=self.id, user_id=current_user.id).first() is None,
            'message_id': self.id,
            'created_at': self.created_at - timedelta(hours=3),
            'responses': sorted([
                {
                    'message': r.message,
                    'likes': r.likes,
                    'dislikes': r.dislikes,
                    'message_id': r.id,
                    'can_vote': not current_user.is_anonymous and \
                                Vote.query.filter_by(message_id=r.id, user_id=current_user.id).first() is None,
                    'created_at': r.created_at - timedelta(hours=3),
                    'id': r.id
                } for r in self.responses], key=lambda r: r['created_at'])
        }
