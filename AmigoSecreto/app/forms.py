# app/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length

class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class GroupForm(FlaskForm):
    name = StringField('Group Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Length(max=300)])
    submit = SubmitField('Create Group')

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length, URL

class GiftForm(FlaskForm):
    gift_name = StringField('Nome do Presente', validators=[DataRequired(), Length(max=255)])
    gift_link = StringField('Link do Presente', validators=[DataRequired(), URL()])
