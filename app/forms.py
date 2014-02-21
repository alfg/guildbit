from flask_wtf import Form
from wtforms import TextField, SelectField, BooleanField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Required, Email


class DeployServerForm(Form):
    duration = SelectField('duration',
                           validators=[DataRequired()],
                           choices=[
                               ('4', '4 Hours'),
                               ('8', '8 Hours'),
                               ('16', '16 Hours'),
                               ('24', '24 Hours')
                           ])
    password = TextField('password', validators=[DataRequired('Password is required.')])


class DeployCustomServerForm(Form):
    slots = IntegerField('slots')
    password = TextField('password', validators=[DataRequired('Password is required.')])
    channel_name = TextField('channel_name')


class LoginForm(Form):
    openid = TextField('openid', validators=[Required()])
    remember_me = BooleanField('remember_me', default=False)


class UserAdminForm(Form):
    role = SelectField('role',
                       validators=[DataRequired()],
                       choices=[
                           ('0', 'User'),
                           ('1', 'Admin')
                       ])


class ContactForm(Form):
    subject = TextField('subject', validators=[DataRequired('Subject is required.')])
    email = TextField('email', validators=[Email('Invalid email address.'), DataRequired('Email is required.')])
    message = TextAreaField('message', validators=[DataRequired('Message is required.')])