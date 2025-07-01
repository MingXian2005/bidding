from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length

class RegistrationForm(FlaskForm):
    IdentificationKey = StringField('Identification Key', validators=[InputRequired(), Length(min=4, max=80)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6, max=120)])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    IdentificationKey = StringField("Identification Key",
            validators=[InputRequired()], render_kw={"placeholder": "Identification Key"})
    password = PasswordField("Password",
            validators=[InputRequired()], render_kw={"placeholder": "Password"})
    
    submit = SubmitField('Login')
