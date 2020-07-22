# main.py

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from project.models import Category

main = Blueprint('main', __name__)


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/profile')
@login_required
def profile():
    categories = Category.query.filter_by(state='available')
    return render_template('profile.html', name=current_user.name, count=categories.count(), categories=categories)
