from app import db
from app.models import User, FlashCard
import sqlalchemy as sa


def reset_and_get_topic_info(user):
    topics = {}
    for card in user.flash_cards:
        if card.topic in topics:
            topics[card.topic][card.id] = {'question': card.question, 'answer': card.answer}
        else:
            topics[card.topic] = {card.id: {'question': card.question, 'answer': card.answer}}

    for card in user.flash_cards:
        card.seen = False
    db.session.commit()
    return topics


def get_user_by_username(name):
    return db.session.scalar(sa.select(User).where(User.username == name))


def calculate_ease(card):
    percent = (card.times_correct / card.times_seen) * 100
    return max(1, int(percent))


def grade_card(card, correct):
    card.times_seen += 1
    if correct:
        card.times_correct += 1
    else:
        card.times_wrong += 1

    card.ease = calculate_ease(card)
    db.session.commit()
    return card
