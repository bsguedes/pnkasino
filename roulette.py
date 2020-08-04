# roulette.py

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from flask_socketio import emit
from apscheduler.schedulers.background import BackgroundScheduler
from app import socket_io, db
from models import User
from random import randint
from threading import Timer



roulette = Blueprint('roulette', __name__)

current_bets = {}
recents = [0] * 10
blocked = [False]


def message_received(json, methods=['GET', 'POST']):
    print('message was received!!!' + json)


@socket_io.on('my event')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    print('received my event: ' + str(json))
    emit('my response', json, callback=message_received)


@socket_io.on('do_bet')
def handle_do_bet_event(json, methods=['GET', 'POST']):
    user_id = json['user_id']
    bet_value = json['bet_value']
    category = json['category']

    payload = {
        'error': None,
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
        payload['error'] = 'Bela tentativa.'
    elif category not in ['btGreen', 'btBlue', 'btRed']:
        payload['error'] = 'Opção inválida.'
    elif int(user_id) in current_bets:
        payload['error'] = 'Aguarde o próximo ciclo de apostas em alguns segundos.'
    elif blocked[0]:
        payload['error'] = 'Aguarde o próximo ciclo de apostas em alguns segundos.'
    else:
        current_bets[int(user_id)] = {'value': int(bet_value), 'category': category}
        current_user.pnkoins -= int(bet_value)
        current_user.roulette_earnings -= int(bet_value)
        db.session.commit()
        payload['user_name'] = current_user.name
        payload['value'] = int(bet_value)
        payload['category'] = category
        payload['new_balance'] = current_user.pnkoins

    emit('bet_cb', payload)


@login_required
@roulette.route('/roulette')
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
    recents.insert(0, number)
    recents.pop(10)
    with app.app_context():
        socket_io.emit('roulette_number', recents)
    winning_category = 'btGreen' if number == 0 else 'btBlue' if number % 2 == 1 else 'btRed'
    multiplier = 14 if winning_category == 'btGreen' else 2
    winners = []
    losers = []
    for user_id, bet_object in current_bets.items():
        with app.app_context():
            if bet_object['category'] == winning_category:
                user = User.query.filter_by(id=user_id).first()
                user.pnkoins += multiplier * bet_object['value']
                user.roulette_earnings += multiplier * bet_object['value']
                db.session.commit()
                winners.append({
                    'winnings': multiplier * bet_object['value'],
                    'new_balance': user.pnkoins,
                    'user_id': str(user_id)
                })
            else:
                losers.append(str(user_id))
    with app.app_context():
        socket_io.emit('winning_message', {'winners': winners, 'losers': losers})
    clear_bets()


def start_roulette():
    scheduler = BackgroundScheduler()
    scheduler.add_job(roulette_hit, 'interval', seconds=16)
    scheduler.start()