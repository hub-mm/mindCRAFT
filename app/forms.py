from flask_wtf import FlaskForm
from wtforms import (SubmitField, HiddenField, StringField, PasswordField,
                     BooleanField, ValidationError, EmailField)
from wtforms.fields.simple import TextAreaField
from wtforms.validators import DataRequired, Length, EqualTo
from email_validator import validate_email, EmailNotValidError
import re


# Validators
def validate_password_complexity(form, field):
    password = field.data
    if not re.search(r'[A-Z]', password):
        raise ValidationError('Password must contain at least one uppercase letter')
    if not re.search(r'[a-z]', password):
        raise ValidationError('Password must contain at least one lowercase letter')
    if not re.search(r'\d', password):
        raise ValidationError('Password must contain at least one digit')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValidationError('Password must contain at least one special character')


def valid_email(form, field):
    email = field.data
    try:
        validate_email(email)
    except EmailNotValidError as e:
        raise ValidationError(f"Email not valid: {e}")


def not_equal(form, field):
    if field.data == form.email.data:
        raise ValidationError('Backup Email must be different from Email')


# Forms
class ChooseForm(FlaskForm):
    delete = HiddenField('Choice')
    change = HiddenField('Choice')
    next = HiddenField('Choice')
    prev = HiddenField('Choice')


class RegisterForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), valid_email])
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long'),
        validate_password_complexity
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class ChangePasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long'),
        validate_password_complexity
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match'),
    ])
    submit = SubmitField('Update Password')


class ChangeEmail(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), valid_email])
    new_email = EmailField('New Email', validators=[DataRequired(), valid_email])
    confirm_email = EmailField('Confirm Email', validators=[
        DataRequired('You must enter and Email'),
        EqualTo('new_email', message='Email\'s must match')
    ])
    submit = SubmitField('Update Email')


class AddFlashCardForm(FlaskForm):
    new = HiddenField(default='-1')
    topic = StringField('Topic', validators=[DataRequired()])
    question = TextAreaField('Question', validators=[DataRequired()])
    answer = TextAreaField('Answer', validators=[DataRequired()])
    submit = SubmitField('Add Flash Card')
