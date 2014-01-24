from flask_wtf import Form
from wtforms import TextField, SelectField, BooleanField
from wtforms.validators import DataRequired, Required


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


class LoginForm(Form):
    openid = TextField('openid', validators=[Required()])
    remember_me = BooleanField('remember_me', default=False)