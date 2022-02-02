from flask import Blueprint, render_template, flash, request, redirect, url_for
from flask_login import login_required, current_user
from models.user import User
from models.scrap import Scrap
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
            current_user.check_achievement(heroes.WRAITH_KING)
            current_user.check_achievement(heroes.DARK_SEER)
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
