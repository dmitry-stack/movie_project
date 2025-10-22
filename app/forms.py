from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, EqualTo, Length, NumberRange, Email

# ======== FORMS =========
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=150)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
   # username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Login')

class MovieForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=150)])
    genre = StringField('Genre', validators=[DataRequired(), Length(max=50)])
    year = IntegerField('Year', validators=[DataRequired(), NumberRange(min=1888, max=2100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    submit = SubmitField('Add Movie')

class ReviewForm(FlaskForm):
    content = TextAreaField('Review', validators=[DataRequired(), Length(max=1000)])
    rating = IntegerField('Rating', validators=[DataRequired(), NumberRange(min=1, max=5)])
    submit = SubmitField('Submit Review')

class RequestResetForm(FlaskForm):
 email = StringField('Email', validators=[DataRequired(), Email()])
 submit = SubmitField('Send Reset Link')

class ResetPasswordForm(FlaskForm):
  password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
  confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
  submit = SubmitField('Reset')

