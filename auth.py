# auth.py

from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from models import User, League
from app import db
import sendgrid
import os
from sqlalchemy import func
from sendgrid.helpers.mail import Email, Content, Mail, To
import random


auth = Blueprint('auth', __name__)
COINS = 43000


@auth.route('/login')
def login():
    return render_template('login.html')


@auth.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password, password):
        flash('Usuário ou senha incorretos')
        return redirect(url_for('auth.login'))

    login_user(user, remember=remember)
    user.last_login = func.now()
    db.session.commit()
    return redirect(url_for('main.profile'))


@auth.route('/signup')
def signup():
    return render_template('signup.html')


@auth.route('/signup', methods=['POST'])
def signup_post():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first()

    if user:
        flash('O endereço de email já está cadastrado')
        return redirect(url_for('auth.signup'))

    league = League.query.filter_by(state='available').first()
    credit = COINS if league is None else league.credit

    new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'),
                    pnkoins=credit, earnings=0, last_login=func.now())

    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('auth.login'))


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@auth.route('/login/redefine')
def redefine():
    code = request.args.get('code')
    user = User.query.filter_by(rec_key=code).first()
    if user is not None:
        return render_template('redefine.html', email=user.email, code=code)
    else:
        flash('Código inválido', 'error')
        return redirect(url_for('auth.login'))


@auth.route('/login/redefine', methods=['POST'])
def redefine_post():
    code = request.form.get('code')
    password = request.form.get('password')
    user = User.query.filter_by(rec_key=code).first()
    if code is not None and user is not None:
        user.password = generate_password_hash(password, method='sha256')
        user.rec_key = None
        db.session.commit()
        flash('Senha redefinida', 'success')
        return redirect(url_for('auth.login'))
    else:
        flash('Ocorreu um erro ao redefinir senha', 'error')
        return redirect(url_for('auth.login'))


@auth.route('/login/forgot')
def forgot():
    return render_template('forgot.html')


@auth.route('/login/forgot', methods=['POST'])
def forgot_post():
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()
    if user:
        h = random.getrandbits(128)
        user.rec_key = "%032x" % h
        db.session.commit()
        sg = sendgrid.SendGridAPIClient(api_key=os.environ['SENDGRID_API_KEY'])
        from_email = Email("PnKasino <pnkasino@gmail.com>")
        subject = "Recuperação de Senha PnKasino!"
        to_email = To(user.email)
        msg = 'Clique no link a seguir para definir uma nova senha.'
        url = '%slogin/redefine?code=%s' % (request.host_url, user.rec_key)
        content = Content("text/html", '%s <br/><br/><a href="%s">%s</a>' % (msg, url, url))
        mail = Mail(from_email, to_email, subject, content)
        sg.client.mail.send.post(request_body=mail.get())
        flash('Instruções de recuperação enviadas', 'success')
        return redirect(url_for('auth.login'))
    else:
        flash('Não foi possível encontrar o jogador', 'error')
        return redirect(url_for('auth.forgot'))

