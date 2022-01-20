# main.py

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models.user import User
from models.category import Category
from models.option import Option
from models.bet import Bet
from models.card import Card
from models.league import League
from admin import league_states
from app import db
from itertools import groupby
from sqlalchemy import func


main = Blueprint('main', __name__)

positions = {
    'hard carry': 1,
    'mid': 2,
    'offlane': 3,
    'support': 4,
    'hard support': 5
}

inv_positions = {v: k for k, v in positions.items()}


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/history')
@login_required
def history():
    user_bets = Bet.query.filter_by(user_id=current_user.id).all()
    bets = sorted([{
                'id': bet.id,
                'question': bet.category.question,
                'option': bet.option.name,
                'bet': bet.value,
                'options': [
                    {'name': bet.category.options[0].name, 'odds': bet.category.options[0].odds},
                    {'name': bet.category.options[1].name, 'odds': bet.category.options[1].odds},
                ],
                'league_name': bet.category.league.name,
                'league_id': bet.category.league_id,
                'league_state': bet.category.league.state,
                'sell_value': int(bet.value * 0.7) if bet.category.league.state == 'available' else None,
                'result': bet.result()
            } for bet in user_bets], key=lambda s: (-s['league_id'], league_states.index(s['league_state'])))

    leagues = [{
        'name': league_name,
        'bets': list(user_bets),
        'ranking': League.query.filter_by(name=league_name).first().ranking()
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

    fantasy_teams = []
    for user in User.query.all():
        pos_1 = card_dict(user.card_1_id, user.buy_1, user)
        pos_2 = card_dict(user.card_2_id, user.buy_2, user)
        pos_3 = card_dict(user.card_3_id, user.buy_3, user)
        pos_4 = card_dict(user.card_4_id, user.buy_4, user)
        pos_5 = card_dict(user.card_5_id, user.buy_5, user)
        player_cards = [pos_1, pos_2, pos_3, pos_4, pos_5]
        if any([p is not None for p in player_cards]):
            price = sum([v['buy_value'] for v in player_cards if v is not None])
            current = sum([v['sell_value'] for v in player_cards if v is not None])
            fantasy_teams.append({
                'name': user.name,
                'price': price,
                'current': current,
                'hard_carry': pos_1['name'] if pos_1 is not None else '',
                'mid': pos_2['name'] if pos_2 is not None else '',
                'offlane': pos_3['name'] if pos_3 is not None else '',
                'support': pos_4['name'] if pos_4 is not None else '',
                'hard_support': pos_5['name'] if pos_5 is not None else '',
                'silver': user.silver_card,
                'gold': user.gold_card,
                'profit': current - price
            })

    return render_template('stats.html',
                           category_chunks=chunks(categories, 3),
                           empty=len(categories) == 0,
                           fantasy_teams=sorted(fantasy_teams, key=lambda e: (-e['profit'], e['current'])))


def card_dict(card_id, bought_at, user):
    if card_id is not None:
        card = Card.query.filter_by(id=card_id).first()
        return {
            'id': card_id,
            'position': inv_positions[card.position].title(),
            'name': card.name,
            'current_value': card.current_value(user),
            'sell_value': card.sell_value(user),
            'buy_value': bought_at
        }
    return None


@main.route('/ranking')
@login_required
def ranking():
    users = User.query.all()
    users_payload = []
    for u, i in zip(sorted(users, key=lambda e: -e.worth()), range(len(users))):
        finished = u.finished_bets_without_cashback()
        on_hold = sum([b.value for b in u.bets if b.category.league.state in ['available', 'blocked']])
        cards = sum(v['sell_value'] for _, v in u.team().items())
        total_earnings = u.earnings + u.roulette_earnings - finished
        user_object = {
            'position': i+1,
            'name': u.name,
            'base': u.pnkoins - total_earnings + on_hold,
            'earnings': u.earnings - finished,
            'roulette': u.roulette_earnings,
            'fantasy': u.fantasy_earnings,
            'total_earnings': total_earnings,
            'pnkoins': u.pnkoins,
            'betted': on_hold,
            'cards': cards,
            'worth': u.worth()
        }
        users_payload.append(user_object)

    performance = sorted(users_payload, key=lambda e: -e['total_earnings'])
    i = 1
    for item in performance:
        item['position_performance'] = i
        item['fantasy_earnings'] = item['fantasy'] + item['cards']
        i += 1

    return render_template('ranking.html', users=users_payload, performance=performance)


@main.route('/bets')
@login_required
def bets():
    leagues = League.query.filter_by(state='available').all()
    categories = []
    for league in leagues:
        for cat in league.categories:
            if not cat.has_winner():
                categories.append(cat)
    categories_betted = [b.category_id for b in Bet.query.filter_by(user=current_user).all()]
    valid_categories = [c for c in categories if c.id not in categories_betted]
    return render_template('bets.html', name=current_user.name,
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
        bet_obj = Bet.query.filter_by(user_id=current_user.id, option_id=option.id, category_id=category_id).first()
        if bet_obj is not None:
            flash('Aposta duplicada', 'error')
        else:
            new_bet = Bet(user_id=current_user.id, option_id=option.id, category_id=category_id, value=int(bet))
            current_user.pnkoins -= int(bet)
            db.session.add(new_bet)
            current_user.last_login = func.now()
            db.session.commit()
            flash('Aposta feita com sucesso', 'success')

    return redirect(url_for('main.bets'))


@main.route('/revert', methods=['POST'])
@login_required
def revert_bet():
    bet_id = int(request.form.get('id'))
    bet = Bet.query.filter_by(id=bet_id).first()

    if bet is None:
        flash('Erro ao reverter aposta', 'error')
    elif bet.user_id != current_user.id:
        flash('Operação inválida', 'error')
    else:
        delta = int(bet.value * 0.7)
        current_user.pnkoins += delta
        current_user.earnings -= (bet.value - delta)
        current_user.last_login = func.now()
        db.session.delete(bet)
        db.session.commit()
        flash('Aposta revertida com sucesso', 'success')
    return redirect(url_for('main.bets'))
