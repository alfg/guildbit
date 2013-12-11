from flask_wtf import Form
from wtforms import TextField, SelectField
from wtforms.validators import DataRequired


class DeployServerForm(Form):
    duration = SelectField('duration',
                           validators=[DataRequired()],
                           choices=[
                               ('0', 'Set a Duration'),
                               ('4', '4 Hours'),
                               ('8', '8 Hours'),
                               ('16', '16 Hours'),
                               ('24', '24 Hours')
                           ])
    password = TextField('password', validators=[DataRequired('Password is required.')])