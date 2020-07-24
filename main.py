# main.py

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import User, Category, Option, Bet
from app import db

main = Blueprint('main', __name__)


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/history')
@login_required
def history():
    user_bets = Bet.query.filter_by(user_id=current_user.id).all()
    bets = [
        {'question': bet.category.question,
         'option': bet.option.name,
         'bet': bet.value,
         'options': [
             {'name': bet.category.options[0].name, 'odds': bet.category.options[0].odds},
             {'name': bet.category.options[1].name, 'odds': bet.category.options[1].odds},
         ],
         'result': bet.result()} for bet in user_bets]
    return render_template('history.html', bets=bets)


@main.route('/ranking')
@login_required
def ranking():
    users = User.query.all()
    user_object = [
        {
            'position': i+1,
            'name': u.name,
            'pnkoins': u.pnkoins,
            'betted': sum([b.value for b in u.bets if b.category.state == 'available'])
        } for u, i in zip(sorted(users, key=lambda u: -u.pnkoins), range(len(users)))]

    return render_template('ranking.html', users=user_object)


@main.route('/profile')
@login_required
def profile():
    categories = Category.query.filter_by(state='available')
    categories_betted = [b.category_id for b in Bet.query.filter_by(user=current_user).all()]
    valid_categories = [c for c in categories.all() if c.id not in categories_betted]
    return render_template('profile.html', name=current_user.name,
                           count=len(valid_categories),
                           categories=valid_categories,
                           pnkoins=current_user.pnkoins)


@main.route('/place', methods=['POST'])
@login_required
def place_post():
    category_id = request.form.get('id')
    bet = request.form.get('bet')
    bet_left = request.form.get('bet1')

    if not bet.isdigit():
        flash('Your bet contains invalid characters.', 'error')
    elif int(bet) > current_user.pnkoins or int(bet) <= 0:
        flash('Your bet exceeds the amount of PnKoins you have.', 'error')
    elif int(bet) > Category.query.filter_by(id=category_id).first().max_bet:
        flash('Your bet exceeds the maximum value for this Event.', 'error')
    else:
        option_query = Option.query.filter_by(category_id=category_id).all()
        option = option_query[0] if bet_left is None else option_query[1]
        new_bet = Bet(user_id=current_user.id, option_id=option.id, category_id=category_id, value=int(bet))
        current_user.pnkoins -= int(bet)
        db.session.add(new_bet)
        db.session.commit()
        flash('Bet placed successfully', 'success')

    return redirect(url_for('main.profile'))
