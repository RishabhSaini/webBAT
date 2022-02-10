 
from flask_wtf import FlaskForm
from flask_wtf.recaptcha import RecaptchaField
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, SelectMultipleField, widgets, DateTimeField, IntegerField, DecimalField, TextAreaField, HiddenField
from wtforms_components import TimeField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from . import models

db = models.db

class SubmitTriggerForm(FlaskForm):
    event_name  = StringField('Name', validators=[DataRequired()])
    trigger_instrument = StringField('Instrument', validators=[DataRequired()])
    types = [(None, 'Select')]
    for a in models.trigger_type:
        types.append((a.name, a.name))
    trigger_type =SelectField('Trigger Type', choices=types, validators=[DataRequired()])

    trigtime = DateTimeField('Trigger Time', format='%Y-%m-%dT%H:%M:%S.%f')

    ra = DecimalField("RA")
    dec = DecimalField("Dec")
    error = DecimalField("Error")
    submit = SubmitField('Submit')