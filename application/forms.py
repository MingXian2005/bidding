from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, IntegerField
from wtforms.validators import InputRequired, Length, NumberRange

class RegistrationForm(FlaskForm):
    IdentificationKey = StringField('Identification Key', validators=[InputRequired(), Length(min=4, max=80)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6, max=120)])
    display_name = StringField('Display Name', validators=[InputRequired(), Length(min=1, max=80)])
    submit = SubmitField('Register')


class BidForm(FlaskForm):
    amount = FloatField('Bid Amount (RM$)', validators=[InputRequired(), NumberRange(min=0.01)])
    submit = SubmitField('Place Bid')


class LoginForm(FlaskForm):
    display_name = StringField('Company Name', 
            validators=[InputRequired()], render_kw={"placeholder": "Company Name"})
    password = PasswordField("Password",
            validators=[InputRequired()], render_kw={"placeholder": "Password"})
    
    submit = SubmitField('Login')


class TimerForm(FlaskForm):
    duration = IntegerField('Auction Duration (minutes)', validators=[InputRequired(), NumberRange(min=1)])
    submit = SubmitField('Set Timer')


class InitialsForm(FlaskForm):
    StartingBid = FloatField('Starting Bid ($)', validators=[InputRequired()])
    BidDecrement = FloatField('Next Bid Decrement($)', validators=[InputRequired()])
    submit = SubmitField('Confirm')
