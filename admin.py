from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import User, Category, Option, Bet, League
from app import db


admin = Blueprint('admin', __name__)


@admin.route('/admin')
@login_required
def index():
    if current_user.is_admin_user():
        return render_template('admin.html', leagues=League.query.all())
    else:
        flash('User is not an admin.', 'error')
        return redirect(url_for('main.profile'))


@admin.route('/league/create', methods=['POST'])
@login_required
def league_create_post():
    league_name = request.form.get('league_name')
    if current_user.is_admin_user():
        new_league = League(name=league_name, state='new')
        db.session.add(new_league)
        db.session.commit()
        flash('League %s created successfully!' % league_name, 'success')
        return redirect(url_for('admin.index'))
    else:
        flash('User is not an admin.', 'error')
        return redirect(url_for('main.profile'))


@admin.route('/league/edit', methods=['POST'])
@login_required
def history():
    league_id = request.form.get('id')
    if current_user.is_admin_user():
        league = League.query.filter_by(id=int(league_id)).all()[0]
        return render_template('edit.html', league=league)
    else:
        flash('User is not an admin.', 'error')
        return redirect(url_for('main.profile'))
