# message.py

from app import db
from datetime import timedelta


class Scrap(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    message = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    parent_scrap_id = db.Column(db.Integer, db.ForeignKey('scrap.id'), nullable=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    author = db.relationship("User", back_populates="scraps", foreign_keys="Scrap.author_id")
    profile_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    responses = db.relationship('Scrap', lazy=True, foreign_keys="Scrap.parent_scrap_id")

    def as_json(self):
        return {
            'message': self.message,
            'scrap_id': self.id,
            'created_at': self.created_at - timedelta(hours=3),
            'latest_at': self.latest_response() - timedelta(hours=3),
            'author_id': self.author_id,
            'author_name': None if self.author is None else self.author.stats_name,
            'is_anonymous': self.author_id is None,
            'responses': sorted([
                {
                    'message': r.message,
                    'scrap_id': r.id,
                    'created_at': r.created_at - timedelta(hours=3),
                    'author_id': r.author_id,
                    'author_name': None if r.author is None else r.author.stats_name,
                    'is_anonymous': r.author_id is None
                } for r in self.responses], key=lambda r: r['created_at'])
        }

    def latest_response(self):
        responses = [r.created_at for r in self.responses]
        responses.append(self.created_at)
        return max(responses)
