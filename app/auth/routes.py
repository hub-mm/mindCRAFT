from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import current_user, login_user, logout_user, login_required
from app import db
from app.forms import LoginForm, ChangePasswordForm, RegisterForm
from app.models import User
from app.utils import get_user_by_username
import sqlalchemy as sa
from urllib.parse import urlsplit

auth_bp = Blueprint('auth', __name__, template_folder='templates/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('flashcards.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = get_user_by_username(form.username.data)
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('flashcards.dashboard')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User()
        user.email = form.email.data
        user.username = form.username.data
        user.set_password(form.password.data)
        user.role = 'Normal'

        existing_user = get_user_by_username(user.username)
        if existing_user:
            flash('Username not available', 'danger')
            return redirect(url_for('.register'))
        existing_email = db.session.scalar((sa.select(User).where(User.email == user.email)))
        if existing_email:
            flash('Email already used', 'danger')
            return redirect(url_for('.register'))

        db.session.add(user)
        db.session.commit()
        flash('Account created successfully, login to proceed', 'success')
        return redirect(url_for('.login'))
    return render_template('register.html', title='Register', form=form)


@auth_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    return render_template(
        'settings.html',
        title='Settings',
    )


@auth_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        user = get_user_by_username(current_user.username)
        if not user.check_password(form.password.data):
            flash('Invalid password', 'danger')
            return redirect(url_for('.change_password'))

        user.set_password(form.new_password.data)
        db.session.commit()
        flash('Password has been changed successfully', 'success')
        return redirect(url_for('public.landing'))

    return render_template('change_password.html', title='Change Password', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('public.landing'))
