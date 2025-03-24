from flask import render_template, redirect, url_for, flash, request, send_file, send_from_directory
from app import app
from app.forms import ChooseForm, LoginForm, ChangePasswordForm, RegisterForm, ChangeEmail
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sa
from app import db
from app.models import User
from urllib.parse import urlsplit


@app.route('/')
def home():
    return render_template('home.html', title='Home')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User()
        user.email = form.email.data
        user.username = form.username.data
        user.set_password(form.password.data)
        user.role = 'Normal'

        existing_user = db.session.scalar(sa.select(User).where(User.username == user.username))
        if existing_user:
            flash('Username not available', 'danger')
            return redirect(url_for('register'))
        existing_email = db.session.scalar((sa.select(User).where(User.email == user.email)))
        if existing_email:
            flash('Email already used', 'danger')
            return redirect(url_for('register'))

        db.session.add(user)
        db.session.commit()
        flash('Account created successfully, login to proceed', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data)
        )
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('home')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    form = ChooseForm()
    if current_user.role != 'Admin':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('home'))

    if form.validate_on_submit():
        try:
            delete_value = int(form.delete.data) if form.delete.data else -1
            change_value = int(form.change.data) if form.change.data else -1
            admin_count = User.query.filter_by(role='Admin').count()

            if (
                    delete_value == current_user.id and admin_count > 1
                    or
                    change_value == current_user.id and admin_count > 1
            ):
                logout_user()

            if delete_value != -1:
                user = User.query.get(delete_value)
                if not user:
                    flash(f"User with ID: {delete_value} does not exist", 'danger')
                    return redirect(url_for('admin'))
                if user.role == 'Admin':
                    if admin_count <= 1:
                        flash('Must have at least one admin', 'danger')
                        return redirect(url_for('admin'))
                db.session.delete(user)
                db.session.commit()
                flash(f"{user.username} has been deleted successfully", 'success')
                return redirect(url_for('admin'))
            elif change_value != -1:
                user = User.query.get(change_value)
                if not user:
                    flash(f"User with ID: {change_value} does not exist", 'danger')
                    return redirect(url_for('admin'))
                if user.role == 'Admin':
                    if admin_count <= 1:
                        flash('Must have at least one admin', 'danger')
                        return redirect(url_for('admin'))
                    user.role = 'Normal'
                else:
                    user.role = 'Admin'
                db.session.commit()
                flash(f"{user.username}'s role has been changed successfully", 'success')
                return redirect(url_for('admin'))
        except Exception as e:
            flash('Error occurred while performing action', 'danger')
            print(f"Error: {e}")

    users = User.query.all()
    headers = ['ID', 'Username', 'Email', 'Role', 'Delete', 'Swap Role']
    return render_template(
        'admin.html',
        title='Admin Page',
        form=form,
        headers=headers,
        users=users
    )


@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    return render_template(
        'account.html',
        title='Account',
    )


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    return render_template(
        'settings.html',
        title='Settings',
    )


@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == current_user.username)
        )
        if not user.check_password(form.password.data):
            flash('Invalid password', 'danger')
            return redirect(url_for('change_password'))

        user.set_password(form.new_password.data)
        db.session.commit()
        flash('Password has been changed successfully', 'success')
        return redirect(url_for('home'))

    return render_template('change_password.html', title='Change Password', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/flash_cards')
def flash_cards():
    return render_template('flash_cards.html', title='Flash Cards')


# Error handlers
# See: https://en.wikipedia.org/wiki/List_of_HTTP_status_codes

# Error handler for 403 Forbidden
@app.errorhandler(403)
def error_403(error):
    return render_template('errors/403.html', title='Error'), 403


# Handler for 404 Not Found
@app.errorhandler(404)
def error_404(error):
    return render_template('errors/404.html', title='Error'), 404


@app.errorhandler(413)
def error_413(error):
    return render_template('errors/413.html', title='Error'), 413


# 500 Internal Server Error
@app.errorhandler(500)
def error_500(error):
    return render_template('errors/500.html', title='Error'), 500
