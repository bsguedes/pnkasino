from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models.user import User
from models.category import Category
from models.option import Option
from models.card import Card
from models.scrap import Scrap
from models.league import League
from models.achievement import Achievement
from models.achievement_user import AchievementUser
from models.message import Message
from models.vote import Vote
from app import db
from sqlalchemy import text
import json
import random
import heroes
import time


admin = Blueprint('admin', __name__)


league_states = ['new', 'available', 'blocked', 'finished']

positions = {
    'hard carry': 1,
    'mid': 2,
    'offlane': 3,
    'support': 4,
    'hard support': 5
}

inv_positions = {v: k for k, v in positions.items()}


@admin.route('/admin')
@login_required
def index():
    if current_user.is_admin_user():
        return render_template('admin.html',
                               leagues=sorted([l.as_json() for l in League.query.all()],
                                              key=lambda s: (league_states.index(s['state']), -s['id'])),
                               users=sorted([u.as_json() for u in User.query.all()],
                                            key=lambda e: e['login'], reverse=True),
                               scraps=[s.as_json() for s in Scrap.query.order_by(text("id desc")).limit(10)],
                               achievements=sorted([a.as_json() for a in Achievement.query.all()],
                                                   key=lambda e: e['earned_count'], reverse=True),
                               amounts={
                                   'scraps': Scrap.query.count(),
                                   'achievements': AchievementUser.query.count(),
                                   'votes': Vote.query.count(),
                                   'book': Message.query.count(),
                               })
    else:
        flash('User is not an admin', 'error')
        return redirect(url_for('main.index'))


@admin.route('/achievement/create', methods=['POST'])
@login_required
def achievement_create_post():
    hero_name = request.form.get('hero_name')
    hero_id = request.form.get('hero_id')
    description = request.form.get('description')
    if current_user.is_admin_user():
        if not hero_id.isdigit():
            flash('Invalid hero id', 'error')
            return redirect(url_for('admin.index'))
        if Achievement.query.filter_by(hero_id=int(hero_id)).first() is not None:
            flash('Hero ID already exists', 'error')
            return redirect(url_for('admin.index'))
        new_achievement = Achievement(hero_id=int(hero_id), hero_name=hero_name, description=description)
        db.session.add(new_achievement)
        db.session.commit()
        flash('Achievement created successfully!', 'success')
        return redirect(url_for('admin.index'))
    else:
        flash('User is not an admin', 'error')
        return redirect(url_for('main.index'))


@admin.route('/league/create', methods=['POST'])
@login_required
def league_create_post():
    league_name = request.form.get('league_name')
    credit = request.form.get('credit')
    if current_user.is_admin_user():
        if not credit.isdigit():
            flash('Invalid credit value', 'error')
            return redirect(url_for('admin.index'))
        new_league = League(name=league_name, credit=credit, state='new')
        db.session.add(new_league)
        db.session.commit()
        flash('League %s created successfully!' % league_name, 'success')
        return redirect(url_for('admin.index'))
    else:
        flash('User is not an admin', 'error')
        return redirect(url_for('main.index'))


@admin.route('/admin/reset', methods=['POST'])
@login_required
def reset_pwd():
    user_id = request.form.get('pwdid')
    if current_user.is_admin_user():
        print(user_id)
        u = User.query.filter_by(id=user_id).first()
        print(u.name)
        if u is None:
            flash('Invalid user', 'error')
            return redirect(url_for('admin.index'))
        h = random.getrandbits(128)
        u.rec_key = "%032x" % h
        db.session.commit()
        flash('Password reset!', 'success')
        return redirect(url_for('admin.index'))
    else:
        flash('User is not an admin', 'error')
        return redirect(url_for('main.index'))


@admin.route('/admin/coins', methods=['POST'])
@login_required
def add_coins():
    credit = request.form.get('credit')
    if current_user.is_admin_user():
        if not credit.isdigit():
            flash('Invalid credit value', 'error')
            return redirect(url_for('admin.index'))
        for user in User.query.all():
            user.add_pnkoins(int(credit))
        db.session.commit()
        flash('Everyone got %s PnKoins!' % credit, 'success')
        return redirect(url_for('admin.index'))
    else:
        flash('User is not an admin', 'error')
        return redirect(url_for('main.index'))


@admin.route('/admin/fantasy/rewards', methods=['POST'])
@login_required
def update_rewards():
    content = request.form.get('rewards')
    if current_user.is_admin_user():
        player_rewards = json.loads(content)['rewards']

        for player in player_rewards:
            user = User.query.filter_by(name=player['name']).first()
            if user is not None:
                prize = player['earnings'] + player['bonus']
                user.add_pnkoins(prize)
                user.fantasy_earnings += prize
                db.session.commit()
                if player['bonus'] == 5000:
                    user.assign_achievement(heroes.LUNA)
        flash('Rewards added', 'success')
        return redirect(url_for('admin.index'))
    else:
        flash('User is not an admin', 'error')
        return redirect(url_for('main.index'))


@admin.route('/admin/fantasy/player', methods=['POST'])
@login_required
def add_player_to_fantasy():
    content = request.form.get('player')
    if current_user.is_admin_user():
        new_player = json.loads(content)['player']
        for position, value in json.loads(content)['roles'].items():
            card = Card.query.filter_by(name=new_player, position=positions[position]).first()
            if card is None:
                new_card = Card(name=new_player, position=positions[position],
                                new_base_value=value, current_delta=0)
                db.session.add(new_card)
                db.session.commit()
            else:
                flash('Player already exists', 'error')
                return redirect(url_for('admin.index'))
        flash('New Player Added', 'success')
        return redirect(url_for('admin.index'))
    else:
        flash('User is not an admin', 'error')
        return redirect(url_for('main.index'))


@admin.route('/admin/fantasy/refund', methods=['POST'])
@login_required
def refund_fantasy():
    starting_value = request.form.get('starting_value')
    if current_user.is_admin_user():
        if not starting_value.isdigit():
            flash('Invalid credit value', 'error')
            return redirect(url_for('admin.index'))
        for user in User.query.all():
            user.refund_cards(int(starting_value))
        return redirect(url_for('admin.index'))
    else:
        flash('User is not an admin', 'error')
        return redirect(url_for('main.index'))


@admin.route('/admin/evaluate', methods=['POST'])
@login_required
def evaluate():
    if current_user.is_admin_user():
        from fantasy import card_value_updated, card_bought, card_gold_silver_updated
        start = time.time()

        for user in User.query.all():
            user.check_achievement(heroes.ALCHEMIST)
            user.check_achievement(heroes.ZEUS)
            user.check_achievement(heroes.MORPHLING)
            user.check_achievement(heroes.WINDRANGER)
            user.check_achievement(heroes.BRISTLEBACK)
            user.check_achievement(heroes.TIMBERSAW)
            user.check_achievement(heroes.SVEN)
            user.check_achievement(heroes.RIKI)
            user.check_achievement(heroes.VIPER)
            user.check_achievement(heroes.CRYSTAL_MAIDEN)
            user.check_achievement(heroes.SAND_KING)

        for card_name in set([c.name for c in Card.query.all()]):
            card_gold_silver_updated(card_name)
            card_bought(card_name, True)

        for card in Card.query.all():
            card_value_updated(card.name, card.value())

        for league in League.query.all():
            ranking = league.ranking()
            if ranking is not None and len(ranking) > 0:
                user = User.query.filter_by(id=ranking[0]['profile_id']).first()
                user.assign_achievement(heroes.MARS)

        flash('Evaluated achievements in  %.3f seconds' % (time.time() - start), 'success')
        return redirect(url_for('admin.index'))
    else:
        flash('User is not an admin', 'error')
        return redirect(url_for('main.index'))


@admin.route('/admin/fantasy', methods=['POST'])
@login_required
def update_fantasy():
    content = request.form.get('json')
    if current_user.is_admin_user():
        parsed_content = json.loads(content)

        for card_in_db in Card.query.all():
            if card_in_db.name in parsed_content and \
                    inv_positions[card_in_db.position] in parsed_content[card_in_db.name] and \
                    parsed_content[card_in_db.name][inv_positions[card_in_db.position]] > 0:
                if card_in_db.current_delta <= 0:
                    card_in_db.current_delta -= 2
                old_value = card_in_db.value()
                new_value = parsed_content[card_in_db.name][inv_positions[card_in_db.position]]
                new_value = (2 * card_in_db.value() + new_value) // 30 * 10
            else:
                old_value = card_in_db.value()
                card_in_db.current_delta -= 5
                new_value = card_in_db.value()
            card_in_db.current_delta = 0
            card_in_db.old_base_value = old_value
            card_in_db.new_base_value = new_value
            db.session.commit()

        for player_name, p in parsed_content.items():
            for position, value in p.items():
                card = Card.query.filter_by(name=player_name, position=positions[position]).first()
                if card is None:
                    new_card = Card(name=player_name, position=positions[position],
                                    new_base_value=value, current_delta=0)
                    db.session.add(new_card)
                    db.session.commit()
        return redirect(url_for('admin.index'))
    else:
        flash('User is not an admin', 'error')
        return redirect(url_for('main.index'))


@admin.route('/admin/winner', methods=['POST'])
@login_required
def winner():
    category_id = request.form.get('id')
    league_id = request.form.get('league_id')
    option_left = request.form.get('option1')
    if current_user.is_admin_user():
        category = Category.query.filter_by(id=category_id).first()
        option = category.options[1] if option_left is None else category.options[0]
        category.winner_option_id = option.id
        db.session.commit()
        flash('Saved result for category', 'success')
        return redirect(url_for('admin.edit', league_id=league_id))
    else:
        flash('User is not an admin', 'error')
        return redirect(url_for('main.index'))


@admin.route('/league/edit/<int:league_id>')
@login_required
def edit(league_id):
    if current_user.is_admin_user():
        league = League.query.filter_by(id=league_id).first()
        return render_template('edit.html', league=league)
    else:
        flash('User is not an admin', 'error')
        return redirect(url_for('main.index'))


@admin.route('/league/edit/name', methods=['POST'])
@login_required
def edit_league_name():
    league_id = request.form.get('id')
    if current_user.is_admin_user():
        try:
            name = request.form.get('name')
            league = League.query.filter_by(id=league_id).first()
            league.name = name
            db.session.commit()
            flash('Name changed', 'success')
            return redirect(url_for('admin.edit', league_id=league_id))
        except:
            flash('Please check your data', 'error')
            return redirect(url_for('admin.edit', league_id=league_id))
    else:
        flash('User is not an admin', 'error')
        return redirect(url_for('main.index'))


@admin.route('/achievement/edit/<int:achievement_id>')
@login_required
def edit_achievement(achievement_id):
    if current_user.is_admin_user():
        achievement = Achievement.query.filter_by(id=achievement_id).first()
        return render_template('achievement.html', achievement=achievement.as_json(),
                               earners=achievement.earners_names())
    else:
        flash('User is not an admin', 'error')
        return redirect(url_for('main.index'))


@admin.route('/achievement/edit/description', methods=['POST'])
@login_required
def edit_achievement_description():
    achievement_id = request.form.get('id')
    if current_user.is_admin_user():
        try:
            description = request.form.get('description')
            achievement = Achievement.query.filter_by(id=achievement_id).first()
            achievement.description = description
            db.session.commit()
            flash('Description changed', 'success')
            return redirect(url_for('admin.edit_achievement', achievement_id=achievement_id))
        except:
            flash('Please check your data', 'error')
            return redirect(url_for('admin.edit_achievement', achievement_id=achievement_id))
    else:
        flash('User is not an admin', 'error')
        return redirect(url_for('main.index'))


@admin.route('/league/addcategory', methods=['POST'])
@login_required
def add_category():
    league_id = request.form.get('id')
    if current_user.is_admin_user():
        try:
            question = request.form.get('question')
            max_bet = int(request.form.get('max_bet'))
            option1 = request.form.get('option1')
            perc_1 = float(request.form.get('odds2'))
            option2 = request.form.get('option2')

            new_category = Category(question=question, max_bet=max_bet, league_id=int(league_id))
            db.session.add(new_category)
            db.session.commit()

            odds1 = int((100 / perc_1) * 100) / 100
            odds2 = int((100 / (100 - perc_1)) * 100) / 100

            new_option1 = Option(name=option1, odds=odds1, category_id=new_category.id)
            new_option2 = Option(name=option2, odds=odds2, category_id=new_category.id)

            db.session.add(new_option1)
            db.session.add(new_option2)
            db.session.commit()
            flash('Category added successfully', 'success')
            return redirect(url_for('admin.edit', league_id=league_id))
        except:
            flash('Please check your data', 'error')
            return redirect(url_for('admin.edit', league_id=league_id))
    else:
        flash('User is not an admin', 'error')
        return redirect(url_for('main.index'))


@admin.route('/league/up', methods=['POST'])
@login_required
def league_up():
    league_id = request.form.get('id')
    if current_user.is_admin_user():
        league = League.query.filter_by(id=int(league_id)).first()
        if league.state == 'new':
            league.state = 'available'
            for user in User.query.all():
                user.add_pnkoins(league.credit)
        elif league.state == 'available':
            league.state = 'blocked'
        elif league.state == 'blocked':
            league.state = 'finished'
            for category in league.categories:
                for bet in category.bets:
                    if bet.option_id == category.winner_option_id:
                        bet.user.earnings += int(category.winner_option().odds * bet.value)
                        bet.user.add_pnkoins(int(category.winner_option().odds * bet.value))
                        bet.user.check_achievement(heroes.TIMBERSAW)
                    elif category.winner_option_id is None:
                        bet.user.add_pnkoins(bet.value)
                    else:
                        bet.user.earnings -= bet.value
            ranking = league.ranking()
            if ranking is not None and len(ranking) > 0:
                winner_player = User.query.filter_by(id=ranking[0]['profile_id']).first()
                winner_player.assign_achievement(heroes.MARS)
            for user in User.query.all():
                user.check_achievement(heroes.SPIRIT_BREAKER)
        else:
            flash('Cannot change league state', 'error')
            return redirect(url_for('admin.index'))
        db.session.commit()
        flash('League state changed successfully', 'success')
        return redirect(url_for('admin.index'))
    else:
        flash('User is not an admin', 'error')
        return redirect(url_for('main.index'))
