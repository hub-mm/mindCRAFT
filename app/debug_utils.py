from app import db
from app.models import User, FlashCard


def reset_db():
    db.drop_all()
    db.create_all()

    u1 = User(username='amy', email='a@b.com', role='Admin')
    u1.set_password('amy.pw')
    u2 = User(username='tom', email='t@b.com')
    u2.set_password('tom.pw')
    u3 = User(username='yin', email='y@b.com', role='Admin')
    u3.set_password('yin.pw')
    u4 = User(username='tariq', email='tariq@b.com')
    u4.set_password('tariq.pw')
    u5 = User(username='jo', email='jo@b.com')
    u5.set_password('jo.pw')

    u1.flash_cards.append(FlashCard(topic='math', question='9 + 10', answer='19'))
    u1.flash_cards.append(FlashCard(topic='math', question='2 + 4', answer='6'))
    u1.flash_cards.append(FlashCard(topic='math', question='5 + 5', answer='10'))

    db.session.add_all([u1, u2, u3, u4, u5])
    db.session.commit()
