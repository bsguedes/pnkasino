# main.py

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import User, Category, Option, Bet, League
from admin import league_states
from app import db
from itertools import groupby


main = Blueprint('main', __name__)


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/history')
@login_required
def history():
    user_bets = Bet.query.filter_by(user_id=current_user.id).all()
    bets = sorted([{
                'question': bet.category.question,
                'option': bet.option.name,
                'bet': bet.value,
                'options': [
                    {'name': bet.category.options[0].name, 'odds': bet.category.options[0].odds},
                    {'name': bet.category.options[1].name, 'odds': bet.category.options[1].odds},
                ],
                'league_name': bet.category.league.name,
                'league_state': bet.category.league.state,
                'result': bet.result()
            } for bet in user_bets], key=lambda s: league_states.index(s['league_state']))
    leagues = [{
        'name': league_name,
        'bets': list(user_bets)
    } for league_name, user_bets in groupby(bets, key=lambda x: x['league_name'])]
    return render_template('history.html', leagues=leagues)


def chunks(l, n):
    n = max(1, n)
    return (l[i:i+n] for i in range(0, len(l), n))


@main.route('/stats')
@login_required
def stats():
    league = League.query.filter_by(state='blocked').first()
    if league is None and current_user.is_admin_user():
        league = League.query.filter_by(state='available').first()
    categories = []
    if league is not None:
        categories = [
            {
                'name': cat.question,
                'bets': len(cat.bets),
                'pnkoins': sum([b.value for b in cat.bets]),
                'options': [
                    {
                        'name': opt.name,
                        'odds': opt.odds,
                        'betters': len(opt.bets),
                        'pnkoins': sum([b.value for b in opt.bets])
                    } for opt in cat.options]
            } for cat in league.categories]

    return render_template('stats.html', category_chunks=chunks(categories, 3), empty=len(categories) == 0)


@main.route('/ranking')
@login_required
def ranking():
    users = User.query.all()
    user_object = [
        {
            'position': i+1,
            'name': u.name,
            'earnings': u.earnings - u.finished_bets_without_cashback(),
            'roulette': u.roulette_earnings,
            'fantasy': u.fantasy_earnings,
            'total_earnings': u.earnings
                              + u.roulette_earnings
                              - u.finished_bets_without_cashback()
                              + u.fantasy_earnings,
            'pnkoins': u.pnkoins,
            'betted': sum([b.value for b in u.bets if b.category.league.state in ['available', 'blocked']])
        } for u, i in zip(sorted(users, key=lambda u: (-u.pnkoins, -(u.earnings + u.roulette_earnings))),
                          range(len(users)))]

    return render_template('ranking.html', users=user_object)


@main.route('/profile')
@login_required
def profile():
    leagues = League.query.filter_by(state='available').all()
    categories = []
    for league in leagues:
        for cat in league.categories:
            if not cat.has_winner():
                categories.append(cat)
    categories_betted = [b.category_id for b in Bet.query.filter_by(user=current_user).all()]
    valid_categories = [c for c in categories if c.id not in categories_betted]
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
        flash('Sua aposta contém caracteres inválidos', 'error')
    elif int(bet) > current_user.pnkoins or int(bet) <= 0:
        flash('Você não tem PnKoins suficientes', 'error')
    elif int(bet) > Category.query.filter_by(id=category_id).first().max_bet:
        flash('Sua aposta excede a aposta máxima para este evento', 'error')
    else:
        option_query = Option.query.filter_by(category_id=category_id).all()
        option = option_query[1] if bet_left is None else option_query[0]
        new_bet = Bet(user_id=current_user.id, option_id=option.id, category_id=category_id, value=int(bet))
        current_user.pnkoins -= int(bet)
        db.session.add(new_bet)
        db.session.commit()
        flash('Aposta feita com sucesso', 'success')

    return redirect(url_for('main.profile'))
