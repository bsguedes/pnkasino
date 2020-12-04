from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import User, Card, League
from app import db
from sqlalchemy import func


fantasy = Blueprint('fantasy', __name__)

positions = {
    'hard carry': 1,
    'mid': 2,
    'offlane': 3,
    'support': 4,
    'hard support': 5
}

inv_positions = {v: k for k, v in positions.items()}


@fantasy.route('/fantasy')
@login_required
def index():
    pos_1 = card_dict(current_user.card_1_id, current_user.buy_1, current_user)
    pos_2 = card_dict(current_user.card_2_id, current_user.buy_2, current_user)
    pos_3 = card_dict(current_user.card_3_id, current_user.buy_3, current_user)
    pos_4 = card_dict(current_user.card_4_id, current_user.buy_4, current_user)
    pos_5 = card_dict(current_user.card_5_id, current_user.buy_5, current_user)
    player_cards = [pos_1, pos_2, pos_3, pos_4, pos_5]
    cards = [c for c in player_cards if c is not None]
    current_players = [c['name'] for c in cards]
    transfer_window_open = League.query.filter_by(state='available').first() is not None
    available_cards = {}
    for i in range(5):
        pos = i + 1
        db_cards = Card.query.filter_by(position=pos)
        available_cards[pos] = chunks(sorted([{
            'id': card.id,
            'name': card.name,
            'position': inv_positions[card.position].title(),
            'current_value': card.value(),
            'state': card_state(card, player_cards[i], current_players, transfer_window_open)
        } for card in db_cards if card.value() > 0], key=lambda e: -e['current_value']), 6)
    silver_upgrades = [
        {
            'id': card['id'],
            'can_upgrade': current_user.silver_card not in [1, 2, 3, 4, 5] and
            current_user.gold_card != card['pos'] and
            current_user.pnkoins >= card['silver_cost'] and
            transfer_window_open,
            'cost': card['silver_cost'],
            'perks': [card['silver_perk']]
        } for card in cards]
    gold_upgrades = [
        {
            'id': card['id'],
            'can_upgrade': current_user.gold_card not in [1, 2, 3, 4, 5] and
            current_user.silver_card != card['pos'] and
            current_user.pnkoins >= card['silver_cost'] and
            transfer_window_open,
            'cost': card['gold_cost'],
            'perks': [card['silver_perk'], card['gold_perk']]
        } for card in cards]
    return render_template('fantasy.html',
                           current_cards=cards,
                           transfer_window_open=transfer_window_open,
                           available_cards=available_cards,
                           silver_upgrades=silver_upgrades,
                           gold_upgrades=gold_upgrades,
                           titles=[k for k, v in positions.items()])


@fantasy.route('/fantasy/summary')
def summary():
    return {'cards': [{
        'name': card.name,
        'position': inv_positions[card.position],
        'current_value': card.value(),
        'old_value': card.old_base_value if card.old_base_value is not None else card.new_base_value,
        'variation': card.value() / (card.new_base_value if (card.old_base_value is None or card.old_base_value == 0)
                                     else card.old_base_value) - 1
    } for card in Card.query.all() if card.new_base_value > 0 and card.value() > 0]}


@fantasy.route('/fantasy/scores')
def scores():
    score_list = []
    for user in User.query.all():
        if user.has_team():
            team = user.team()
            cost = sum(t['buy_value'] for p, t in team.items())
            score = sum(t['points'] for p, t in team.items())
            u = {
                'name': user.name,
                'real_name': user.stats_name,
                'team': team,
                'cost': cost,
                'silver': user.silver_card,
                'gold': user.gold_card,
                'total_score': score,
                'earnings': int(score ** 3) // 100 * 10,
                'worth': user.worth()
            }
            score_list.append(u)
    return {'scores': sorted(score_list, key=lambda e: (-e['total_score'], e['cost']))}


@fantasy.route('/fantasy/buy', methods=['POST'])
@login_required
def buy():
    card_id = request.form.get('id')

    card = Card.query.filter_by(id=card_id).first()

    if card is None:
        flash('Não foi possível comprar a carta', 'error')
    elif current_user.pnkoins < card.value():
        flash('Você não tem PnKoins suficientes', 'error')
    elif current_user.has_card(card.position):
        flash('Você já tem uma carta para esta posição', 'error')
    elif current_user.has_player(card.name):
        flash('Você já tem esse jogador no seu time', 'error')
    else:
        current_user.set_card(card)
        current_user.pnkoins -= card.value()
        current_user.fantasy_earnings -= card.value()
        card.current_delta += 1
        current_user.last_login = func.now()
        db.session.commit()
        flash('Seu time agora tem %s como %s' % (card.name, inv_positions[card.position]), 'success')

    return redirect(url_for('fantasy.index'))


@fantasy.route('/fantasy/silver', methods=['POST'])
@login_required
def silver():
    card_id = request.form.get('id')

    card = Card.query.filter_by(id=card_id).first()

    if card is None:
        flash('Não foi possível atualizar a carta', 'error')
    elif current_user.pnkoins < card.silver_cost():
        flash('Você não tem PnKoins suficientes', 'error')
    elif current_user.silver_card == card.position:
        flash('Você já tem uma carta Prata para esta posição', 'error')
    else:
        current_user.set_additional_buy_cost(card, card.silver_cost())
        current_user.silver_card = card.position
        current_user.pnkoins -= card.silver_cost()
        current_user.fantasy_earnings -= card.silver_cost()
        card.current_delta += 1
        current_user.last_login = func.now()
        db.session.commit()
        flash('Você promoveu o %s %s para Prata!' % (card.name, inv_positions[card.position]), 'success')

    return redirect(url_for('fantasy.index'))


@fantasy.route('/fantasy/gold', methods=['POST'])
@login_required
def gold():
    card_id = request.form.get('id')

    card = Card.query.filter_by(id=card_id).first()

    if card is None:
        flash('Não foi possível atualizar a carta', 'error')
    elif current_user.pnkoins < card.gold_cost():
        flash('Você não tem PnKoins suficientes', 'error')
    elif current_user.gold_card == card.position:
        flash('Você já tem uma carta Ouro para esta posição', 'error')
    else:
        current_user.set_additional_buy_cost(card, card.gold_cost())
        current_user.gold_card = card.position
        current_user.pnkoins -= card.gold_cost()
        current_user.fantasy_earnings -= card.gold_cost()
        card.current_delta += 1
        current_user.last_login = func.now()
        db.session.commit()
        flash('Você promoveu o %s %s para Ouro!' % (card.name, inv_positions[card.position]), 'success')

    return redirect(url_for('fantasy.index'))


@fantasy.route('/fantasy/sell', methods=['POST'])
@login_required
def sell():
    card_id = request.form.get('id')

    card = Card.query.filter_by(id=card_id).first()

    if card is None:
        flash('Não foi possível vender a carta', 'error')
    elif not current_user.has_card(card.position):
        flash('Você não tem a carta marcada para venda', 'error')
    elif not current_user.has_player(card.name):
        flash('Você não tem a carta marcada para venda', 'error')
    else:
        current_user.pnkoins += card.sell_value(current_user)
        current_user.fantasy_earnings += card.sell_value(current_user)
        was_promoted = current_user.clear_card(card)
        card.current_delta -= 2 if was_promoted else 1
        current_user.last_login = func.now()
        db.session.commit()
        flash('Você vendeu o %s %s' % (inv_positions[card.position], card.name), 'success')

    return redirect(url_for('fantasy.index'))


def card_state(card_db, card_obj, current_players, transfer_window_open):
    if not transfer_window_open:
        return 'blocked'
    elif card_obj is None:
        if card_db.name in current_players:
            return 'owned_player'
        return 'buy' if current_user.pnkoins >= card_db.value() else 'no_funds'
    else:
        if card_obj['name'] == card_db.name:
            return 'owned'
        return 'must_sell' if current_user.pnkoins >= card_db.value() else 'no_funds'


def card_dict(card_id, bought_at, user):
    if card_id is not None:
        card = Card.query.filter_by(id=card_id).first()
        return {
            'id': card_id,
            'position': inv_positions[card.position].title(),
            'pos': card.position,
            'name': card.name,
            'current_value': card.current_value(user),
            'sell_value': card.sell_value(user),
            'buy_value': bought_at,
            'silver_cost': card.silver_cost(),
            'silver_perk': card.silver_perk(),
            'gold_cost': card.gold_cost(),
            'gold_perk': card.gold_perk(),
            'is_silver': card.position == user.silver_card,
            'is_gold': card.position == user.gold_card,
            'color': card.color(user.silver_card, user.gold_card)
        }
    return None


def chunks(l, n):
    n = max(1, n)
    return (l[i:i+n] for i in range(0, len(l), n))
