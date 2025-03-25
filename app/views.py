from flask import render_template, redirect, url_for, flash, request, send_file, send_from_directory
from app import app
from app.forms import ChooseForm, LoginForm, ChangePasswordForm, RegisterForm, ChangeEmail
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sa
from app import db
from app.models import User, FlashCard
from urllib.parse import urlsplit
from datetime import datetime
import random


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
    topics = set(card.topic for card in current_user.flash_cards)
    return render_template(
        'flash_cards.html',
        title='Flash Cards',
        topics=topics
    )


@app.route('/flash_cards/<topic>/<hashed_id>/<show>', methods=['POST', 'GET'])
def flash_cards_by_topic(topic, hashed_id, show):
    cards = [card for card in current_user.flash_cards if card.topic == topic]
    if not cards:
        flash('No cards exists for this topic.', 'danger')
        return redirect(url_for('flash_cards'))

    card = None
    if hashed_id != 'next':
        card_id = FlashCard.decode_hashed_id(hashed_id)
        if card_id:
            card = next((card for card in cards if card.id == card_id), None)

    if card is None:
        unseen_cards = [card for card in cards if not card.seen]
        if not unseen_cards:
            for card in cards:
                card.seen = False
            db.session.commit()
            unseen_cards = cards
        card = random.choice(unseen_cards)

    card.seen = True
    card.last_seen = datetime.now()
    db.session.commit()

    form = ChooseForm()
    return render_template(
        'flash_cards_topic.html',
        title=f"{topic.title()} Flash Cards",
        topic=topic,
        hashed_id=card.hashed_id,
        show=show,
        card=card,
        form=form
    )


@app.route('/flip_card/<topic>/<hashed_id>/<show>', methods=['POST', 'GET'])
def flip_card(topic, hashed_id, show):
    new_show = 'answer' if show == 'question' else 'question'
    return redirect(url_for(
        'flash_cards_by_topic',
        topic=topic,
        hashed_id=hashed_id,
        show=new_show
    ))


@app.route('/previous_card/<topic>/<hashed_id>/<show>', methods=['POST', 'GET'])
def previous_card(topic, hashed_id, show):
    cards = [card for card in current_user.flash_cards if card.topic == topic]
    seen_cards = sorted(cards, key=lambda card: card.last_seen)
    prev_card_hashed_id = seen_cards[-2].hashed_id
    return redirect(url_for(
        'flash_cards_by_topic',
        topic=topic,
        hashed_id=prev_card_hashed_id,
        show='question'
    ))


@app.route('/next_card/<topic>/<hashed_id>/<show>', methods=['POST', 'GET'])
def next_card(topic, hashed_id, show):
    return redirect(url_for(
        'flash_cards_by_topic',
        topic=topic,
        hashed_id='next',
        show='question'
    ))


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
