from flask_wtf import Form
from wtforms import TextField, SelectField, BooleanField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Required, Email, Length
from flask.ext.babel import lazy_gettext as __

from settings import MURMUR_HOSTS, PACKAGES


def build_hosts_list():
    hosts_list = []
    for i in MURMUR_HOSTS:
        for k, v in i.iteritems():
            if k == "location" and i['status'] == 'active':
                hosts_list.append((v, i['location_name']))
    return hosts_list


def build_packages_list():
    packages_list = []
    for i in PACKAGES:
        for k, v in i.iteritems():
            if k == "name":
                packages_list.append((v, i['name']))
    return packages_list


def duration_choices():
    choices = [
        ('4', '4 %s' % __('Hours')),
        ('8', '8 %s' % __('Hours')),
        ('16', '16 %s' % __('Hours')),
        ('24', '24 %s' % __('Hours'))
    ]
    return choices


class DeployServerForm(Form):
    _server_locations = build_hosts_list()

    location = SelectField('location',
                           validators=[DataRequired()],
                           choices=_server_locations)
    # duration = SelectField('duration')  # Create dynamic list in view
    duration = SelectField('duration',
                           validators=[DataRequired()],
                           choices=[
                               ('4', '4 Hours'),
                               ('8', '8 Hours'),
                               ('16', '16 Hours'),
                               ('24', '24 Hours')
                           ])
    password = TextField('password',
                         validators=[DataRequired('Password is required.'),
                                     Length(min=3, max=25, message="Password must be between 3 and 25 characters long.")])


class DeployCustomServerForm(Form):
    _server_locations = build_hosts_list()

    location = SelectField('location',
                           validators=[DataRequired()],
                           choices=_server_locations)
    slots = IntegerField('slots', default=10)
    password = TextField('password', validators=[DataRequired('Password is required.')])
    channel_name = TextField('channel_name')


class DeployTokenServerForm(Form):
    _server_locations = build_hosts_list()

    location = SelectField('location',
                           validators=[DataRequired()],
                           choices=_server_locations)
    password = TextField('password',
                         validators=[DataRequired('Password is required.'),
                                     Length(min=3, max=25, message="Password must be between 3 and 25 characters long.")])
    channel_name = TextField('channel_name', validators=[DataRequired('Channel name is required.')])


class CreateTokenForm(Form):
    _packages = build_packages_list()

    package = SelectField('package',
                          validators=[DataRequired()],
                          choices=_packages)


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


class NoticeForm(Form):
    message = TextField('message', validators=[DataRequired()])
    active = BooleanField('active')
    message_type = SelectField('type', validators=[DataRequired()],
                       choices=[
                           ('primary', 'primary'),
                           ('secondary', 'secondary'),
                           ('default', 'default'),
                           ('info', 'info'),
                           ('danger', 'danger'),
                           ('warning', 'warning'),
                           ('success', 'success')
                       ])


class SendChannelMessageForm(Form):
    _server_locations = build_hosts_list()

    message = TextField('message', validators=[DataRequired()])
    location = SelectField('location',
                           validators=[DataRequired()],
                           choices=_server_locations)


class SuperuserPasswordForm(Form):
    _server_locations = build_hosts_list()
    password = TextField('password',
                         validators=[DataRequired('Password is required.'),
                                     Length(min=3, max=25, message="Password must be between 3 and 25 characters long.")])
    location = SelectField('location',
                           validators=[DataRequired()],
                           choices=_server_locations)
    instance = IntegerField('instance')


class ContactForm(Form):
    subject = TextField('subject', validators=[DataRequired('Subject is required.')])
    email = TextField('email', validators=[Email('Invalid email address.'), DataRequired('Email is required.')])
    message = TextAreaField('message', validators=[DataRequired('Message is required.')])

