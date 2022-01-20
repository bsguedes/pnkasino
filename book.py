from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models.message import Message
from models.vote import Vote
from app import db
from sqlalchemy import func
from datetime import timedelta


MAX_MESSAGE_LENGTH = 255

book = Blueprint('book', __name__)


@book.route('/book')
def index():
    message_list = reversed(sorted([
        {
            'message': m.message,
            'likes': m.likes,
            'dislikes': m.dislikes,
            'can_vote': not current_user.is_anonymous and Vote.query.filter_by(message_id=m.id, user_id=current_user.id).first() is None,
            'message_id': m.id,
            'created_at': m.created_at - timedelta(hours=3),
            'responses': sorted([
                {
                    'message': r.message,
                    'likes': r.likes,
                    'dislikes': r.dislikes,
                    'message_id': r.id,
                    'can_vote': not current_user.is_anonymous and Vote.query.filter_by(message_id=r.id, user_id=current_user.id).first() is None,
                    'created_at': r.created_at - timedelta(hours=3),
                    'id': r.id
                } for r in m.responses], key=lambda r: r['created_at'])
        } for m in Message.query.all() if m.parent_message_id is None],
        key=lambda m: m['created_at']))
    return render_template('book.html', messages=message_list)


@book.route('/book/create', methods=['POST'])
def create():
    message = request.form.get('book_message')
    if len(message) <= MAX_MESSAGE_LENGTH:
        new_message = Message(message=message, created_at=func.now(), likes=0, dislikes=0, parent_message_id=None)
        db.session.add(new_message)
        db.session.commit()
        flash('Mensagem enviada!', 'success')
        return redirect(url_for('book.index'))
    else:
        flash('A mensagem é muito longa.', 'error')
        return redirect(url_for('book.index'))


@book.route('/book/reply', methods=['POST'])
def reply():
    message = request.form.get('book_reply')
    parent_message_id = request.form.get('id')
    parent_message = Message.query.filter_by(id=parent_message_id).first()

    if len(message) <= MAX_MESSAGE_LENGTH:
        new_message = Message(message=message, created_at=func.now(), likes=0, dislikes=0,
                              parent_message_id=parent_message.id)
        db.session.add(new_message)
        db.session.commit()
        flash('Resposta enviada!', 'success')
        return redirect(url_for('book.index'))
    else:
        flash('A resposta é muito longa.', 'error')
        return redirect(url_for('book.index'))


@book.route('/book/vote', methods=['POST'])
@login_required
def vote():
    message_id = request.form.get('id')
    user_id = current_user.id

    check_vote = Vote.query.filter_by(message_id=message_id, user_id=user_id).first()
    if check_vote is not None:
        flash('Você já opinou nesta mensagem.', 'error')
        return redirect(url_for('book.index'))

    upvote = request.form.get('upvote_message')
    message = Message.query.filter_by(id=message_id).first()
    if upvote is None:
        message.dislikes += 1
    else:
        message.likes += 1

    new_vote = Vote(message_id=message_id, user_id=user_id)
    db.session.add(new_vote)
    db.session.commit()
    return redirect(url_for('book.index'))
