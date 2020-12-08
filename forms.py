from datetime import datetime

from flask_wtf import FlaskForm
from wtforms.fields.html5 import DateField, TimeField
from wtforms import PasswordField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(min=8, max=50)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=50)])
    submit = SubmitField("Login")


class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(min=8, max=50)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=50),
                                                     EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Repeat Password')
    submit = SubmitField("Register")


class NoteForm(FlaskForm):
    note = TextAreaField('Note', validators=[DataRequired(), Length(min=4, max=2048)])
    submit = SubmitField("Submit")


class OlderNotesForm(FlaskForm):
    date = DateField("Date", validators=[DataRequired()], default=datetime.today)
    time = TimeField("Time", validators=[DataRequired()], default=datetime.now().time())
    submit = SubmitField("Get Older Notes")
