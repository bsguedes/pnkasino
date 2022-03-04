from flask import Blueprint, render_template, flash, request, redirect, url_for
from flask_login import login_required, current_user
from models.user import User
from models.scrap import Scrap
from models.friendship import Friendship
import heroes
from sqlalchemy import func
from app import db

MAX_MESSAGE_LENGTH = 255

prfl = Blueprint('prfl', __name__)


@prfl.route('/profile/<int:user_id>')
@login_required
def index(user_id):
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        flash('Perfil não encontrado.', 'error')
        return redirect(url_for('prfl.index', user_id=current_user.id))

    current_user.assign_achievement(heroes.DRAGON_KNIGHT)

    if user_id != current_user.id:
        user.profile_views += 1
        db.session.commit()
        user.check_achievement(heroes.SNIPER)
    else:
        last_scrap_id = 0 if len(current_user.scraps) == 0 else max([s.id for s in current_user.scraps])
        if last_scrap_id is not None:
            user.last_scrap_seen = last_scrap_id
            db.session.commit()

    user_profile = user.profile_json()
    return render_template('profile.html', user=user_profile,
                           current_user_name=current_user.stats_name,
                           friend_state=current_user.friend_state(user),
                           pending_requests=current_user.pending_friendships(),
                           has_hero_pool=(len(user_profile['achievements']) > 0))


@prfl.route('/profile/<int:user_id>/scrap', methods=['POST'])
def scrap(user_id):
    message = request.form.get('scrap_message')
    user = User.query.filter_by(id=user_id).first()
    is_anonymous = request.form.get('anonymous_scrap')
    if user is None:
        flash('Perfil não encontrado.', 'error')
        return redirect(url_for('prfl.index', user_id=current_user.id))
    if 0 < len(message) <= MAX_MESSAGE_LENGTH:
        author_id = None if is_anonymous else current_user.id
        new_scrap = Scrap(message=message, created_at=func.now(), parent_scrap_id=None,
                          author_id=author_id, profile_id=user_id)
        db.session.add(new_scrap)
        db.session.commit()
        if author_id is not None:
            current_user.check_achievement(heroes.RIKI)
            current_user.check_achievement(heroes.WRAITH_KING)
            current_user.check_achievement(heroes.DARK_SEER)
        user.check_achievement(heroes.VIPER)
        user.check_achievement(heroes.MARCI)
        user.check_achievement(heroes.HOODWINK)
        flash('Scrap enviado!', 'success')
        return redirect(url_for('prfl.index', user_id=user_id))
    else:
        flash('Tamanho inválido de mensagem.', 'error')
        return redirect(url_for('prfl.index', user_id=user_id))


@prfl.route('/profile/<int:user_id>/reply', methods=['POST'])
def reply(user_id):
    message = request.form.get('scrap_response')
    parent_scrap_id = request.form.get('id')
    user = User.query.filter_by(id=user_id).first()
    parent_scrap = Scrap.query.filter_by(id=parent_scrap_id).first()
    is_anonymous = request.form.get('anonymous_reply')

    if user is None:
        flash('Perfil não encontrado.', 'error')
        return redirect(url_for('prfl.index', user_id=current_user.id))
    if 0 < len(message) <= MAX_MESSAGE_LENGTH:
        author_id = None if is_anonymous else current_user.id
        new_scrap = Scrap(message=message, created_at=func.now(), parent_scrap_id=parent_scrap.id,
                          author_id=author_id, profile_id=user_id)
        db.session.add(new_scrap)
        db.session.commit()
        flash('Resposta enviada!', 'success')
        return redirect(url_for('prfl.index', user_id=user_id))
    else:
        flash('Tamanho inválido de mensagem.', 'error')
        return redirect(url_for('prfl.index', user_id=user_id))


@prfl.route('/profile/<int:user_id>/add', methods=['POST'])
def add(user_id):
    # add a friend from their profile
    return inner_add(user_id, user_id)


@prfl.route('/profile/<int:user_id>/remove', methods=['POST'])
def remove(user_id):
    # remove a friend from their profile
    return inner_remove(user_id, user_id)


@prfl.route('/profile/<int:user_id>/add/self', methods=['POST'])
def add_self(user_id):
    # accept a friend request
    return inner_add(user_id, current_user.id)


@prfl.route('/profile/<int:user_id>/remove/self', methods=['POST'])
def remove_self(user_id):
    # refuse a friend request
    return inner_remove(user_id, current_user.id)


def inner_add(user_id, redirect_id):
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        flash('Perfil não encontrado.', 'error')
        return redirect(url_for('prfl.index', user_id=current_user.id))
    friendship_out = Friendship.query.filter_by(friend_id=current_user.id, invited_id=user.id).first()
    friendship_in = Friendship.query.filter_by(friend_id=user.id, invited_id=current_user.id).first()

    if friendship_out is None:
        friendship_out = Friendship(friend_id=current_user.id, invited_id=user.id,
                                    state='pending', created_at=func.now())
        db.session.add(friendship_out)

    if friendship_in is not None:
        friendship_in.state = 'friend'
        friendship_out.state = 'friend'

    db.session.commit()
    if user_id == redirect_id:
        current_user.assign_achievement(heroes.LONE_DRUID)
    else:
        current_user.assign_achievement(heroes.ORACLE)

    current_user.check_achievement(heroes.CHEN)
    user.check_achievement(heroes.CHEN)

    flash('Adicionou %s aos amigos!' % user.name, 'success')
    return redirect(url_for('prfl.index', user_id=redirect_id))


def inner_remove(user_id, redirect_id):
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        flash('Perfil não encontrado.', 'error')
        return redirect(url_for('prfl.index', user_id=current_user.id))
    friendship_out = Friendship.query.filter_by(friend_id=current_user.id, invited_id=user.id).first()
    friendship_in = Friendship.query.filter_by(friend_id=user.id, invited_id=current_user.id).first()

    if friendship_out is not None:
        db.session.delete(friendship_out)

    if friendship_in is not None:
        db.session.delete(friendship_in)

    db.session.commit()
    flash('Removeu %s dos amigos!' % user.name, 'success')
    return redirect(url_for('prfl.index', user_id=redirect_id))
