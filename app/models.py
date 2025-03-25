from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask_login import UserMixin
from sqlalchemy import ForeignKey
from sqlalchemy.testing.schema import mapped_column
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login, get_serializer
from dataclasses import dataclass
from datetime import datetime


@dataclass
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    role: so.Mapped[str] = so.mapped_column(sa.String(24), nullable=False, default='Normal')
    flash_cards: so.Mapped[list['FlashCard']] = relationship(back_populates='user', cascade='all, delete-orphan')

    def __repr__(self):
        return f"User(id={self.id}, username={self.username}, email={self.email}, role={self.role})"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))


@dataclass
class FlashCard(db.Model):
    __tablename__ = 'flash_cards'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    topic: so.Mapped[str] = so.mapped_column(sa.String(24), index=True, nullable=False)
    question: so.Mapped[str] = so.mapped_column(sa.Text, nullable=False)
    answer: so.Mapped[str] = so.mapped_column(sa.Text, nullable=False)
    seen: so.Mapped[bool] = so.mapped_column(sa.Boolean, nullable=False, default=False)
    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(sa.DateTime, default=None)

    user_id: so.Mapped[int] = so.mapped_column(ForeignKey('users.id'), index=True)
    user: so.Mapped['User'] = relationship(back_populates='flash_cards')

    @property
    def hashed_id(self):
        s = get_serializer()
        return s.dumps(self.id)

    @classmethod
    def decode_hashed_id(cls, token):
        s = get_serializer()
        try:
            original_id = s.loads(token)
            return original_id
        except Exception:
            return None
