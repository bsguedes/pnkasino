# user.py

from flask import url_for
from flask_login import UserMixin
from sqlalchemy.sql.functions import session_user
from sqlalchemy import func
from app import db
import heroes
from models.card import Card
from models.league import League
from models.bet import Bet
from models.message import Message
from models.achievement_user import AchievementUser
from models.achievement import Achievement
from models.friendship import Friendship
from datetime import timedelta, date


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000), nullable=False)
    rec_key = db.Column(db.String(1000), nullable=True)
    pnkoins = db.Column(db.Integer, nullable=False)
    fcoins = db.Column(db.Integer, nullable=False)
    roulette_streak = db.Column(db.Integer, nullable=False)
    login_count = db.Column(db.Integer, nullable=False)
    profile_views = db.Column(db.Integer, nullable=False)
    earnings = db.Column(db.Integer, default=0, nullable=False)
    rewards_earnings = db.Column(db.Integer, default=0, nullable=False)
    roulette_earnings = db.Column(db.Integer, default=0, nullable=False)
    roulette_attempts = db.Column(db.Integer, default=0, nullable=False)
    fantasy_earnings = db.Column(db.Integer, default=0, nullable=False)
    bets = db.relationship('Bet', backref='user', lazy=True)
    last_login = db.Column(db.DateTime)
    last_seen = db.Column(db.DateTime)
    last_fantasy_at = db.Column(db.DateTime)
    last_message_seen = db.Column(db.Integer)
    last_scrap_seen = db.Column(db.Integer)
    achievements_seen = db.Column(db.Integer)
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
    achievement_users = db.relationship('AchievementUser', backref='user', lazy=True)
    scraps = db.relationship('Scrap', foreign_keys='Scrap.profile_id', backref='user', lazy=True)
    scraps_written = db.relationship('Scrap', foreign_keys='Scrap.author_id', lazy=True)
    votes = db.relationship('Vote', foreign_keys='Vote.user_id', backref='user', lazy=True)
    friends = db.relationship('Friendship', foreign_keys='Friendship.invited_id', backref='user', lazy=True)

    def as_json(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'coins': self.pnkoins,
            'dota_name': self.stats_name if self.stats_name is not None else "-",
            'login': (self.last_login - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M") if self.last_login is not None
            else '-',
            'seen': (self.last_seen - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M") if self.last_seen is not None
            else '-',
            'rec_url': self.rec_url()
        }

    def rec_url(self):
        if self.rec_key is not None:
            return '%s?code=%s' % (url_for('auth.redefine'), self.rec_key)
        return None

    def profile_json(self):
        return {
            'id': self.id,
            'dota_name': self.name if self.stats_name is None else self.stats_name,
            'name': '' if self.name == self.stats_name or self.stats_name is None else self.name,
            'pnkoins': self.pnkoins,
            'fcoins': self.fcoins,
            'friends': [f.as_json() for f in self.friends if f.state == 'friend'],
            'achievements': sorted([au.as_json() for au in self.achievement_users],
                                   key=lambda e: e['created_at'], reverse=True),
            'scraps': sorted([s.as_json() for s in self.scraps if s.parent_scrap_id is None],
                             key=lambda e: e['latest_at'], reverse=True)
        }

    def pending_friendships(self):
        return [{
            'id': f.friend_id,
            'name': f.friend.stats_name,
        } for f in Friendship.query.filter_by(invited_id=self.id, state='pending')]

    def friend_state(self, target_user):
        if self.id == target_user.id:
            return None
        user_added = Friendship.query.filter_by(friend_id=self.id, invited_id=target_user.id).first()
        user_invited = Friendship.query.filter_by(friend_id=target_user.id, invited_id=self.id).first()
        if user_added is None and user_invited is None:
            # no friendship exists, I can add this person
            return 'can_add'
        elif user_added is not None and user_invited is not None:
            # friendship already exists
            return 'friend'
        if user_invited is None:
            # I've already added, they haven't accepted yet
            return 'pending_out' if user_added.state == 'pending' else 'can_add'
        if user_added is None:
            # they added me, they haven't accepted yet
            return 'pending_in' if user_invited.state == 'pending' else 'can_add'

    def unread_scraps(self):
        last_scrap_seen = self.last_scrap_seen if self.last_scrap_seen is not None else 0
        return len([1 for scrap in self.scraps if scrap.id > last_scrap_seen]) + len(self.pending_friendships())

    def unread_messages(self):
        last_message_seen = self.last_message_seen if self.last_message_seen is not None else 0
        return len([1 for message in Message.query.all() if message.id > last_message_seen])

    def unseen_achievements(self):
        achievements_seen = self.achievements_seen if self.achievements_seen is not None else 0
        return len(self.achievement_users) - achievements_seen

    def open_bets_count(self):
        leagues = League.query.filter_by(state='available').all()
        categories = []
        for league in leagues:
            for cat in league.categories:
                if not cat.has_winner():
                    categories.append(cat)
        categories_betted = [b.category_id for b in Bet.query.filter_by(user_id=self.id).all()]
        valid_categories = [c for c in categories if c.id not in categories_betted]
        return len(valid_categories)

    def notification_text(self):
        self.last_seen = func.now()
        db.session.commit()
        if self.can_recruit():
            return '!'
        count = self.open_bets_count() + self.unread_messages() + self.unread_scraps()
        if count > 0:
            return count

    def can_recruit(self):
        has_available_league = League.query.filter_by(state='available').first() is not None
        missing_team = not self.has_full_team()
        modified_this_month = not(self.last_fantasy_at is None or self.last_fantasy_at.month != date.today().month)
        if not has_available_league:
            return False
        if missing_team:
            return True
        if modified_this_month:
            return False
        return True

    def assign_achievement(self, hero_id):
        achievement = Achievement.query.filter_by(hero_id=hero_id).first()
        if achievement is not None:
            achievement_id = achievement.id
            if AchievementUser.query.filter_by(user_id=self.id, achievement_id=achievement_id).first() is None:
                AchievementUser.give_achievement(self.id, achievement_id)

    def check_achievement(self, hero_id):
        achievement = Achievement.query.filter_by(hero_id=hero_id).first()
        if achievement is not None:
            achievement_id = achievement.id
            if AchievementUser.query.filter_by(user_id=self.id, achievement_id=achievement_id).first() is None:
                if hero_id == heroes.ALCHEMIST:
                    if self.pnkoins >= 100000:
                        AchievementUser.give_achievement(self.id, achievement_id)
                elif hero_id == heroes.ZEUS:
                    if self.fcoins + self.team_value() >= 18000:
                        AchievementUser.give_achievement(self.id, achievement_id)
                elif hero_id == heroes.MORPHLING:
                    if len(self.votes) >= 20:
                        AchievementUser.give_achievement(self.id, achievement_id)
                elif hero_id == heroes.WINDRANGER:
                    if self.roulette_earnings >= 20000:
                        AchievementUser.give_achievement(self.id, achievement_id)
                elif hero_id == heroes.OGRE_MAGI:
                    if self.roulette_streak >= 4:
                        AchievementUser.give_achievement(self.id, achievement_id)
                elif hero_id == heroes.SVEN:
                    if len(self.bets) >= 1:
                        AchievementUser.give_achievement(self.id, achievement_id)
                elif hero_id == heroes.BRISTLEBACK:
                    if len(self.bets) >= 50:
                        AchievementUser.give_achievement(self.id, achievement_id)
                elif hero_id == heroes.TIMBERSAW:
                    if self.correct_bets() >= 50:
                        AchievementUser.give_achievement(self.id, achievement_id)
                elif hero_id == heroes.SNIPER:
                    if self.profile_views >= 100:
                        AchievementUser.give_achievement(self.id, achievement_id)
                elif hero_id == heroes.RIKI:
                    if len(self.scraps_written) >= 1:
                        AchievementUser.give_achievement(self.id, achievement_id)
                elif hero_id == heroes.WRAITH_KING:
                    if len(self.scraps_written) >= 30:
                        AchievementUser.give_achievement(self.id, achievement_id)
                elif hero_id == heroes.DARK_SEER:
                    if len(set([s.profile_id for s in self.scraps_written])) >= 10:
                        AchievementUser.give_achievement(self.id, achievement_id)
                elif hero_id == heroes.MARCI:
                    if len([s.id for s in self.scraps if s.author_id != self.id]) >= 20:
                        AchievementUser.give_achievement(self.id, achievement_id)
                elif hero_id == heroes.VIPER:
                    if len([s.id for s in self.scraps if s.author_id != self.id]) >= 1:
                        AchievementUser.give_achievement(self.id, achievement_id)
                elif hero_id == heroes.HOODWINK:
                    if len(set([s.author_id for s in self.scraps if s.author_id != self.id])) >= 5:
                        AchievementUser.give_achievement(self.id, achievement_id)
                elif hero_id == heroes.CRYSTAL_MAIDEN:
                    if self.roulette_attempts >= 1:
                        AchievementUser.give_achievement(self.id, achievement_id)
                elif hero_id == heroes.SKYWRATH_MAGE:
                    if self.roulette_attempts >= 100:
                        AchievementUser.give_achievement(self.id, achievement_id)
                elif hero_id == heroes.DARK_WILLOW:
                    if self.login_count >= 10:
                        AchievementUser.give_achievement(self.id, achievement_id)
                elif hero_id == heroes.SAND_KING:
                    if self.has_team():
                        AchievementUser.give_achievement(self.id, achievement_id)
                elif hero_id == heroes.SPIRIT_BREAKER:
                    if self.bets_earnings() >= 25000:
                        AchievementUser.give_achievement(self.id, achievement_id)
                elif hero_id == heroes.CHEN:
                    if len(self.friends) >= 10:
                        AchievementUser.give_achievement(self.id, achievement_id)
                else:
                    return False
        return False

    def correct_bets(self):
        return len([b for b in self.bets if b.correct_winner()])

    def add_pnkoins(self, coins):
        self.pnkoins += coins
        db.session.commit()
        self.check_achievement(heroes.ALCHEMIST)

    def add_fcoins(self, coins):
        self.fcoins += coins
        db.session.commit()
        self.check_achievement(heroes.ZEUS)

    def team_value(self):
        return sum(v['sell_value'] for _, v in self.team().items())

    def has_achievement(self, achievement_id):
        for achievement_user in self.achievement_users:
            if achievement_user.achievement_id == achievement_id:
                return True
        return False

    def finished_bets_without_cashback(self):
        return sum([b.value for b in self.bets if b.category.league.state == 'finished' and b.correct_winner()])

    def bets_on_hold(self):
        return sum([b.value for b in self.bets if b.category.league.state in ['available', 'blocked']])

    def total_earnings(self):
        return self.roulette_earnings + self.rewards_earnings + self.bets_earnings()

    def is_admin_user(self):
        return self.is_admin == 1

    def bets_earnings(self):
        return self.earnings - self.finished_bets_without_cashback()

    def has_team(self):
        v = [self.card_1_id, self.card_2_id, self.card_3_id, self.card_4_id, self.card_5_id]
        return any(x is not None for x in v)

    def has_full_team(self):
        v = [self.card_1_id, self.card_2_id, self.card_3_id, self.card_4_id, self.card_5_id]
        return all(x is not None for x in v)

    def worth(self):
        on_hold = sum([b.value for b in self.bets if b.category.league.state in ['available', 'blocked']])
        return self.pnkoins + on_hold

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

    def card_at_position(self, position):
        if position == 1:
            return self.card_1_id
        elif position == 2:
            return self.card_2_id
        elif position == 3:
            return self.card_3_id
        elif position == 4:
            return self.card_4_id
        elif position == 5:
            return self.card_5_id
        return None

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

    @staticmethod
    def profile_id(card_name):
        user = User.query.filter_by(stats_name=card_name).first()
        return user.id if user is not None else None

    def refund_cards(self, new_starting_value):
        buy1 = self.buy_1 if self.buy_1 is not None else 0
        buy2 = self.buy_2 if self.buy_2 is not None else 0
        buy3 = self.buy_3 if self.buy_3 is not None else 0
        buy4 = self.buy_4 if self.buy_4 is not None else 0
        buy5 = self.buy_5 if self.buy_5 is not None else 0
        refund_value = buy1 + buy2 + buy3 + buy4 + buy5
        self.buy_1 = None
        self.buy_2 = None
        self.buy_3 = None
        self.buy_4 = None
        self.buy_5 = None
        self.gold_card = None
        self.silver_card = None
        self.card_1_id = None
        self.card_2_id = None
        self.card_3_id = None
        self.card_4_id = None
        self.card_5_id = None
        self.fantasy_earnings = 0
        self.add_pnkoins(refund_value)
        self.fcoins = new_starting_value
        db.session.commit()
