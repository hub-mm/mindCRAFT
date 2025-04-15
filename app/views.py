from flask import render_template, redirect, url_for, flash, request
from app import app
from app.forms import ChooseForm, LoginForm, ChangePasswordForm, RegisterForm, ChangeEmail, AddFlashCardForm
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sa
from app import db
from app.models import User, FlashCard
from urllib.parse import urlsplit
from datetime import datetime
import random


# Helper Functions
def reset_and_get_topic_info():
    topics = {}
    for card in current_user.flash_cards:
        if card.topic in topics:
            topics[card.topic][card.id] = {'question': card.question, 'answer': card.answer}
        else:
            topics[card.topic] = {card.id: {'question': card.question, 'answer': card.answer}}

    for card in current_user.flash_cards:
        card.seen = False
    db.session.commit()
    return topics


# Not Logged In Access & Logged In Access
@app.route('/')
def home():
    return render_template('home.html', title='Home')


# Not Logged In Access
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
        return redirect(url_for('user_home'))
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
            next_page = url_for('user_home')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


# Admin Access
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


# User Access
@app.route('/user_home', methods=['POST', 'GET'])
@login_required
def user_home():
    card_date = [card.last_seen.date() if card.last_seen else None for card in current_user.flash_cards]
    today = datetime.now().date()
    cards_today = card_date.count(today)
    cards_total = len(card_date)
    cards_percent_complete = round((cards_today / cards_total) * 100) if cards_total != 0 else 0
    cards_info = {
        'today': today,
        'cards_total': cards_total,
        'cards_today': cards_today,
        'cards_percent_complete': cards_percent_complete
    }
    return render_template(
        'user_home.html',
        title=f"Home {current_user.username}",
        cards_info=cards_info
    )


@app.route('/delete_card', methods=['POST', 'GET'])
def delete_card():
    form = AddFlashCardForm()
    if form.delete.data != '-1':
        card = db.session.get(FlashCard, form.delete.data)
        db.session.delete(card)
        db.session.commit()
        return redirect(url_for('flash_cards'))
    return redirect(url_for('flash_cards'))


@app.route('/add_to_topic', methods=['POST', 'GET'])
def add_to_topic():
    topics = reset_and_get_topic_info()
    form = AddFlashCardForm()
    if form.new.data != '-1' and not form.submit.data:
        card = db.session.get(FlashCard, form.new.data)
        card_form = AddFlashCardForm(topic=card.topic.title())
        return render_template(
            'flash_cards.html',
            title='Flash Cards',
            topics=topics,
            form=card_form,
            mode='new'
        )

    if form.submit.data and form.validate_on_submit():
        new_card = FlashCard(
            topic=form.topic.data.lower().strip(),
            question=form.question.data.strip(),
            answer=form.answer.data.strip()
        )
        current_user.flash_cards.append(new_card)
        db.session.commit()
        return redirect(url_for('flash_cards'))
    return redirect(url_for('flash_cards'))


@app.route('/edit_card', methods=['POST', 'GET'])
def edit_card():
    topics = reset_and_get_topic_info()
    form = AddFlashCardForm()
    if form.edit_question.data != '-1' and not form.submit_edit.data:
        card = db.session.get(FlashCard, form.edit_question.data)
        card_form = AddFlashCardForm(
            topic=card.topic.title(),
            question=card.question.capitalize(),
            answer=card.answer.capitalize()
        )
        return render_template(
            'flash_cards.html',
            title='Flash Cards',
            topics=topics,
            form=card_form,
            topic_edit=card.topic,
            mode='edit'
        )

    if form.submit_edit.data and form.validate_on_submit():
        card = db.session.get(FlashCard, form.edit_question.data)
        card.topic = form.topic.data.lower().strip()
        card.question = form.question.data.strip()
        card.answer = form.answer.data.strip()
        db.session.commit()
        return redirect(url_for('flash_cards'))


@app.route('/flash_cards', methods=['POST', 'GET'])
@login_required
def flash_cards():
    topics = reset_and_get_topic_info()
    form = AddFlashCardForm()
    if form.validate_on_submit():
        topic = form.topic.data.lower().strip()
        question = form.question.data.strip()
        answer = form.answer.data.strip()
        card = FlashCard(topic=topic, question=question, answer=answer)
        current_user.flash_cards.append(card)
        db.session.commit()
        return redirect(url_for('flash_cards'))

    return render_template(
        'flash_cards.html',
        title='Flash Cards',
        topics=topics,
        form=form,
        mode='normal'
    )


@app.route('/flash_cards/<topic>/<hashed_id>/<show>', methods=['POST', 'GET'])
@login_required
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
        if any(card.last_seen for card in cards):
            seen_cards = sorted(cards, key=lambda card: card.last_seen or datetime.min)
            last_seen_card = seen_cards[-1] if seen_cards else None
            if len(cards) > 1:
                while last_seen_card and card.id == last_seen_card.id:
                    card = random.choice(unseen_cards)

    if not card.seen:
        card.last_seen = datetime.now()
    card.seen = True
    db.session.commit()
    complete = len(cards) - len([card for card in cards if not card.seen])

    form = ChooseForm()
    return render_template(
        'flash_cards_topic.html',
        title=f"{topic.title()} Flash Cards",
        topic=topic,
        hashed_id=card.hashed_id,
        show=show,
        card=card,
        total=len(cards),
        complete=complete,
        form=form
    )


@app.route('/flip_card/<topic>/<hashed_id>/<show>', methods=['POST', 'GET'])
@login_required
def flip_card(topic, hashed_id, show):
    new_show = 'answer' if show == 'question' else 'question'
    return redirect(url_for(
        'flash_cards_by_topic',
        topic=topic,
        hashed_id=hashed_id,
        show=new_show
    ))


@app.route('/previous_card/<topic>/<hashed_id>/<show>', methods=['POST', 'GET'])
@login_required
def previous_card(topic, hashed_id, show):
    cards = [card for card in current_user.flash_cards if card.topic == topic]
    seen_cards = sorted([card for card in cards if card.last_seen is not None],
                        key=lambda card: card.last_seen)
    current_card_id = FlashCard.decode_hashed_id(hashed_id)

    current_index = None
    for i, card in enumerate(seen_cards):
        if card.id == current_card_id:
            current_index = i
            break
    if current_index is None:
        current_index = len(seen_cards) - 1

    prev_index = (current_index - 1) % len(seen_cards)
    prev_card = seen_cards[prev_index]
    prev_card_hashed_id = prev_card.hashed_id

    return redirect(url_for(
        'flash_cards_by_topic',
        topic=topic,
        hashed_id=prev_card_hashed_id,
        show='question'
    ))


@app.route('/next_card/<topic>/<hashed_id>/<show>', methods=['POST', 'GET'])
@login_required
def next_card(topic, hashed_id, show):
    return redirect(url_for(
        'flash_cards_by_topic',
        topic=topic,
        hashed_id='next',
        show='question'
    ))


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
