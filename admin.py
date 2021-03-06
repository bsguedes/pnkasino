from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import User, Category, Option, Card, League
from app import db
from datetime import timedelta
import json


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

next_state = {
    'new': 'available',
    'available': 'blocked',
    'blocked': 'finished',
    'finished': None
}


@admin.route('/admin')
@login_required
def index():
    if current_user.is_admin_user():
        return render_template('admin.html', leagues=sorted([
            {
                'id': l.id,
                'name': l.name,
                'state': l.state,
                'credit': l.credit,
                'next_state': next_state[l.state],
                'unset': len([c for c in l.categories if c.winner_option_id is None])
            } for l in League.query.all()], key=lambda s: league_states.index(s['state'])),
                               users=sorted([
                                   {
                                       'name': u.name,
                                       'coins': u.pnkoins,
                                       'login': str(u.last_login - timedelta(hours=3))
                                                if u.last_login is not None else "-"
                                   } for u in User.query.all()
                               ], key=lambda e: e['login'], reverse=True))
    else:
        flash('User is not an admin', 'error')
        return redirect(url_for('main.profile'))


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
        return redirect(url_for('main.profile'))


@admin.route('/admin/coins', methods=['POST'])
@login_required
def add_coins():
    credit = request.form.get('credit')
    if current_user.is_admin_user():
        if not credit.isdigit():
            flash('Invalid credit value', 'error')
            return redirect(url_for('admin.index'))
        for user in User.query.all():
            user.pnkoins += int(credit)
        db.session.commit()
        flash('Everyone got %s PnKoins!' % credit, 'success')
        return redirect(url_for('admin.index'))
    else:
        flash('User is not an admin', 'error')
        return redirect(url_for('main.profile'))


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
                user.pnkoins += prize
                user.fantasy_earnings += prize
                db.session.commit()
        flash('Rewards added', 'success')
        return redirect(url_for('admin.index'))
    else:
        flash('User is not an admin', 'error')
        return redirect(url_for('main.profile'))


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
        return redirect(url_for('main.profile'))


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
        return redirect(url_for('main.profile'))


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
        return redirect(url_for('main.profile'))


@admin.route('/league/edit/<int:league_id>')
@login_required
def edit(league_id):
    if current_user.is_admin_user():
        league = League.query.filter_by(id=league_id).first()
        return render_template('edit.html', league=league)
    else:
        flash('User is not an admin', 'error')
        return redirect(url_for('main.profile'))


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
        return redirect(url_for('main.profile'))


@admin.route('/league/up', methods=['POST'])
@login_required
def league_up():
    league_id = request.form.get('id')
    if current_user.is_admin_user():
        league = League.query.filter_by(id=int(league_id)).first()
        if league.state == 'new':
            league.state = 'available'
            for user in User.query.all():
                user.pnkoins += league.credit
        elif league.state == 'available':
            league.state = 'blocked'
        elif league.state == 'blocked':
            league.state = 'finished'
            for category in league.categories:
                for bet in category.bets:
                    if bet.option_id == category.winner_option_id:
                        bet.user.pnkoins += int(category.winner_option().odds * bet.value)
                        bet.user.earnings += int(category.winner_option().odds * bet.value)
                    elif category.winner_option_id is None:
                        bet.user.pnkoins += bet.value
                    else:
                        bet.user.earnings -= bet.value
        else:
            flash('Cannot change league state', 'error')
            return redirect(url_for('admin.index'))
        db.session.commit()
        flash('League state changed successfully', 'success')
        return redirect(url_for('admin.index'))
    else:
        flash('User is not an admin', 'error')
        return redirect(url_for('main.profile'))
