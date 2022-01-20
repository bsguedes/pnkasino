from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models.message import Message
from models.user import User
from app import db
from sqlalchemy import func
from datetime import timedelta


profile = Blueprint('profile', __name__)


@profile.route('/profile/<:user_id>')
@login_required
def index(user_id):
    user = User.query.filter_by(id=user_id).first()
    return render_template('profile.html', user={
        'dota_name': user.stats_name,
        'name': user.name,
        'pnkoins': user.pnkoins,
        'fcoins': user.fcoins,
    })
