from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import User, Category, Option, Bet, League
from app import db


admin = Blueprint('admin', __name__)


league_states = ['new', 'available', 'blocked', 'finished']

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
            } for l in League.query.all()], key=lambda s: league_states.index(s['state'])))
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
            odds1 = float(request.form.get('odds1'))
            odds2 = float(request.form.get('odds2'))
            option2 = request.form.get('option2')

            new_category = Category(question=question, max_bet=max_bet, league_id=int(league_id))
            db.session.add(new_category)
            db.session.commit()

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
