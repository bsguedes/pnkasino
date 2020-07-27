from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import User, Category, Option, Bet, League
from app import db


admin = Blueprint('admin', __name__)


@admin.route('/admin')
@login_required
def index():
    if current_user.is_admin_user():
        return render_template('admin.html')
    else:
        flash('User is not an admin.', 'error')
        return redirect(url_for('main.profile'))
