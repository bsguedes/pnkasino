# roulette.py

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from apscheduler.schedulers.background import BackgroundScheduler
from app import socket_io, db
from models.user import User
from random import randint
from threading import Timer
from sqlalchemy import func
import heroes


roulette = Blueprint('roulette', __name__)

current_bets = {}
recent_numbers = [-1] * 10
blocked = [False]


def message_received(json, methods=['GET', 'POST']):
    print('message was received!!!' + json)


@socket_io.on('do_bet')
def handle_do_bet_event(json, methods=['GET', 'POST']):
    user_id = json['user_id']
    bet_value = json['bet_value']
    category = json['category']

    payload = {
        'error': None,
        'user_id': user_id,
        'user_name': '',
        'value': 0,
        'category': '',
        'new_balance': 0
    }

    if not user_id.isdigit():
        payload['error'] = 'Usuário incorreto.'
    elif not bet_value.isdigit():
        payload['error'] = 'Valor de aposta inválido.'
    elif int(bet_value) > current_user.pnkoins or int(bet_value) <= 0:
        payload['error'] = 'Aposta maior que o número de PnKoins do jogador.'
    elif category not in ['btGreen', 'btBlue', 'btRed']:
        payload['error'] = 'Opção inválida.'
    elif int(user_id) in current_bets:
        payload['error'] = 'Aguarde o próximo ciclo de apostas em alguns segundos.'
    elif blocked[0]:
        payload['error'] = 'Aguarde o próximo ciclo de apostas em alguns segundos.'
    else:
        current_bets[int(user_id)] = {'value': int(bet_value), 'category': category}
        current_user.add_pnkoins(-int(bet_value))
        current_user.roulette_earnings -= int(bet_value)
        current_user.last_login = func.now()
        db.session.commit()
        payload['user_name'] = current_user.name
        payload['value'] = int(bet_value)
        payload['category'] = category
        payload['new_balance'] = current_user.pnkoins

    socket_io.emit('bet_cb', payload)


@roulette.route('/roulette')
@login_required
def index():
    return render_template('roulette.html')


def clear():
    current_bets.clear()
    blocked[0] = False


def clear_bets():
    from app import app
    with app.app_context():
        socket_io.emit('clear')
    r = Timer(5.0, clear)
    r.start()


def roulette_hit():
    blocked[0] = True
    from app import app
    number = randint(0, 14)
    recent_numbers.insert(0, number)
    recent_numbers.pop(10)
    with app.app_context():
        socket_io.emit('roulette_number', recent_numbers)
    winning_category = 'btGreen' if number == 0 else 'btBlue' if number % 2 == 1 else 'btRed'
    multiplier = 14 if winning_category == 'btGreen' else 2
    winners = []
    losers = []
    for user_id, bet_object in current_bets.items():
        with app.app_context():
            if bet_object['category'] == winning_category:
                user = User.query.filter_by(id=user_id).first()
                user.add_pnkoins(multiplier * bet_object['value'])
                user.roulette_earnings += multiplier * bet_object['value']
                user.roulette_streak += 1
                db.session.commit()
                user.check_achievement(heroes.WINDRANGER)
                user.check_achievement(heroes.OGRE_MAGI)
                if winning_category == 'btGreen':
                    user.assign_achievement(heroes.SNAPFIRE)
                winners.append({
                    'winnings': multiplier * bet_object['value'],
                    'new_balance': user.pnkoins,
                    'user_id': str(user_id)
                })
            else:
                user = User.query.filter_by(id=user_id).first()
                user.roulette_streak = 0
                db.session.commit()
                losers.append(str(user_id))
    with app.app_context():
        socket_io.emit('winning_message', {'winners': winners, 'losers': losers})
    clear_bets()


def start_roulette():
    scheduler = BackgroundScheduler()
    scheduler.add_job(roulette_hit, 'interval', seconds=16)
    print('Roulette Started')
    scheduler.start()
