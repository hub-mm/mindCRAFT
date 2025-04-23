from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import current_user, login_required
from app import db
from app.forms import ChooseForm, AddFlashCardForm
from app.models import FlashCard
from app.utils import reset_and_get_topic_info, grade_card
import sqlalchemy as sa
from datetime import datetime
import random

flashcards_bp = Blueprint('flashcards', __name__, template_folder='templates/flashcards')


@flashcards_bp.route('/dashboard', methods=['POST', 'GET'])
@login_required
def dashboard():
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
    revision = db.session.scalars(
        sa.select(FlashCard).where(FlashCard.ease <= 75).where(FlashCard.user_id == current_user.id)
    ).all()
    return render_template(
        'dashboard.html',
        title=f"Home {current_user.username}",
        cards_info=cards_info,
        revision=revision
    )


@flashcards_bp.route('/delete_card', methods=['POST', 'GET'])
@login_required
def delete_card():
    form = AddFlashCardForm()
    if form.delete.data != '-1':
        card = db.session.get(FlashCard, form.delete.data)
        db.session.delete(card)
        db.session.commit()
        return redirect(url_for('.flashcards'))
    return redirect(url_for('.flashcards'))


@flashcards_bp.route('/add_to_topic', methods=['POST', 'GET'])
@login_required
def add_to_topic():
    topics = reset_and_get_topic_info(current_user)
    form = AddFlashCardForm()
    if form.new.data != '-1' and not form.submit.data:
        card = db.session.get(FlashCard, form.new.data)
        card_form = AddFlashCardForm(topic=card.topic.title())
        return render_template(
            'flashcards.html',
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
        return redirect(url_for('.flashcards'))
    return redirect(url_for('.flashcards'))


@flashcards_bp.route('/edit_card', methods=['POST', 'GET'])
@login_required
def edit_card():
    topics = reset_and_get_topic_info(current_user)
    form = AddFlashCardForm()
    if form.edit_question.data != '-1' and not form.submit_edit.data:
        card = db.session.get(FlashCard, form.edit_question.data)
        card_form = AddFlashCardForm(
            topic=card.topic.title(),
            question=card.question.capitalize(),
            answer=card.answer.capitalize()
        )
        return render_template(
            'flashcards.html',
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
        return redirect(url_for('.flashcards'))


@flashcards_bp.route('/topics', methods=['POST', 'GET'])
@login_required
def flashcards():
    topics = reset_and_get_topic_info(current_user)
    topics['revision'] = {
        card.id: {
            'topic': card.topic, 'question': card.question, 'answer': card.answer
        } for card in current_user.flash_cards if card.ease <= 75
    }
    revision_topics = set(info['topic'] for card_id, info in topics['revision'].items())
    for rev_topic in revision_topics:
        topics[f"revision - {rev_topic}"] = {
            card_id: {
                'topic': info['topic'], 'question': info['question'], 'answer': info['answer']
            } for card_id, info in topics['revision'].items() if info['topic'] == rev_topic
        }

    form = AddFlashCardForm()
    if form.validate_on_submit():
        topic = form.topic.data.lower().strip()
        question = form.question.data.strip()
        answer = form.answer.data.strip()
        card = FlashCard(topic=topic, question=question, answer=answer)
        current_user.flash_cards.append(card)
        db.session.commit()
        return redirect(url_for('.flashcards'))

    return render_template(
        'flashcards.html',
        title='Flash Cards',
        topics=topics,
        form=form,
        mode='normal'
    )


@flashcards_bp.route('/<topic>/<hashed_id>/<show>', methods=['POST', 'GET'])
@login_required
def view_topic(topic, hashed_id, show):
    if topic == 'revision':
        cards = [card for card in current_user.flash_cards if card.ease <= 75]
    elif '-' in topic:
        before, sep, after = topic.partition('-')
        cards = [card for card in current_user.flash_cards if card.topic == after.strip() and card.ease <= 75]
    else:
        cards = [card for card in current_user.flash_cards if card.topic == topic]

    if not cards:
        flash('No cards exists for this topic.', 'danger')
        return redirect(url_for('.flashcards'))

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
        'topic.html',
        title=f"{topic.title()} Flash Cards",
        topic=topic,
        hashed_id=card.hashed_id,
        show=show,
        card=card,
        total=len(cards),
        complete=complete,
        form=form
    )


@flashcards_bp.route('/flip_card/<topic>/<hashed_id>/<show>', methods=['POST', 'GET'])
@login_required
def flip_card(topic, hashed_id, show):
    new_show = 'answer' if show == 'question' else 'question'
    return redirect(url_for(
        '.view_topic',
        topic=topic,
        hashed_id=hashed_id,
        show=new_show
    ))


@flashcards_bp.route('/previous_card/<topic>/<hashed_id>/<show>', methods=['POST', 'GET'])
@login_required
def previous_card(topic, hashed_id, show):
    if topic == 'revision':
        cards = [card for card in current_user.flash_cards if card.ease <= 75]
    else:
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
        '.view_topic',
        topic=topic,
        hashed_id=prev_card_hashed_id,
        show='question'
    ))


@flashcards_bp.route('/next_card/<topic>/<hashed_id>/<show>', methods=['POST', 'GET'])
@login_required
def next_card(topic, hashed_id, show):
    return redirect(url_for(
        '.view_topic',
        topic=topic,
        hashed_id='next',
        show='question'
    ))


@flashcards_bp.route('/card_correct/<topic>/<hashed_id>/<show>', methods=['POST', 'GET'])
@login_required
def card_correct(topic, hashed_id, show):
    card_id = FlashCard.decode_hashed_id(hashed_id)
    card = db.session.scalar(
        sa.select(FlashCard).where(FlashCard.id == card_id).where(FlashCard.user_id == current_user.id)
    ) or abort(404)
    grade_card(card, True)
    return redirect(url_for(
        '.view_topic',
        topic=topic,
        hashed_id=hashed_id,
        show='question'
    ))


@flashcards_bp.route('/card_wrong/<topic>/<hashed_id>/<show>', methods=['POST', 'GET'])
@login_required
def card_wrong(topic, hashed_id, show):
    card_id = FlashCard.decode_hashed_id(hashed_id)
    card = db.session.scalar(
        sa.select(FlashCard).where(FlashCard.id == card_id).where(FlashCard.user_id == current_user.id)
    ) or abort(404)
    grade_card(card, False)
    return redirect(url_for(
        '.view_topic',
        topic=topic,
        hashed_id=hashed_id,
        show='question'
    ))
