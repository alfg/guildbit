import re
from flask_wtf import Form
from wtforms import TextField, SelectField, BooleanField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Required, Email, Length, Regexp
from flask_babel import lazy_gettext as __

from settings import MURMUR_HOSTS, PACKAGES


def get_all_hosts():
    hosts_list = []
    for i in MURMUR_HOSTS:
        for k, v in i.items():
            if k == "location":
                hosts_list.append((v, i['location_name']))
    return hosts_list

def get_active_hosts():
    hosts_list = []
    for i in MURMUR_HOSTS:
        for k, v in i.items():
            if k == "location" and i['active'] == True:
                hosts_list.append((v, i['location_name']))
    return hosts_list

def build_packages_list():
    packages_list = []
    for i in PACKAGES:
        for k, v in i.items():
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
    _server_locations = get_active_hosts()

    location = SelectField('location',
                           validators=[DataRequired()],
                           choices=_server_locations)
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
                                     Regexp("^[A-Za-z0-9_-]*$", re.IGNORECASE, message="Password must be letters and/or numbers only."),
                                     Length(min=3, max=25,
                                            message="Password must be between 3 and 25 characters long.")])


class DeployCustomServerForm(Form):
    _server_locations = get_active_hosts()

    location = SelectField('location',
                           validators=[DataRequired()],
                           choices=_server_locations)
    slots = IntegerField('slots', default=15)
    password = TextField('password', validators=[DataRequired('Password is required.')])
    channel_name = TextField('channel_name')


class DeployTokenServerForm(Form):
    """
    Form used for creating upgraded server (premium users).
    """

    _server_locations = get_active_hosts()

    location = SelectField('location',
                           validators=[DataRequired()],
                           choices=_server_locations)
    password = TextField('password',
                         validators=[DataRequired('Password is required.'),
                                     Regexp("^[A-Za-z0-9_-]*$", re.IGNORECASE, message="Password must be letters and/or numbers only."),
                                     Length(min=3, max=25,
                                            message="Password must be between 3 and 25 characters long.")])
    channel_name = TextField('channel_name', validators=[DataRequired('Channel name is required.')])
    superuser_password = TextField('password',
                                   validators=[DataRequired('Password is required.'),
                                               Length(min=3, max=25,
                                                      message="Password must be between 3 and 25 characters long.")])


class CreateTokenForm(Form):
    _packages = build_packages_list()

    email = TextField('email')
    package = SelectField('package',
                          validators=[DataRequired()],
                          choices=_packages)

class CreateHostForm(Form):
    name = TextField('name', validators=[DataRequired('Name is required.')])
    hostname = TextField('hostname', validators=[DataRequired('Hostname is required.')])
    region = TextField('location', validators=[DataRequired('Location is required.')])
    uri = TextField('uri', validators=[DataRequired('URI is required.')])
    username = TextField('username')
    password = TextField('password')
    type = SelectField('type',
                        validators=[DataRequired()],
                        choices=[
                            ('0', 'Free'),
                            ('1', 'Upgrade')
                        ])

class HostAdminForm(Form):
    name = TextField('name', validators=[DataRequired('Name is required.')])
    hostname = TextField('hostname', validators=[DataRequired('Hostname is required.')])
    region = TextField('location', validators=[DataRequired('Location is required.')])
    uri = TextField('uri', validators=[DataRequired('URI is required.')])
    active = BooleanField('active', default=False)
    username = TextField('username')
    password = TextField('password')

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
    _server_locations = get_all_hosts()

    message = TextField('message', validators=[DataRequired()])
    location = SelectField('location',
                           validators=[DataRequired()],
                           choices=_server_locations)


class SuperuserPasswordForm(Form):
    _server_locations = get_all_hosts()
    password = TextField('password',
                         validators=[DataRequired('Password is required.'),
                                     Length(min=3, max=25,
                                            message="Password must be between 3 and 25 characters long.")])
    location = SelectField('location',
                           validators=[DataRequired()],
                           choices=_server_locations)
    instance = IntegerField('instance')


class CleanupExpiredServersForm(Form):
    _server_locations = get_all_hosts()
    location = SelectField('location',
                           validators=[DataRequired()],
                           choices=_server_locations)


class ContactForm(Form):
    subject = TextField('subject', validators=[DataRequired('Subject is required.')])
    email = TextField('email', validators=[Email('Invalid email address.'), DataRequired('Email is required.')])
    message = TextAreaField('message', validators=[DataRequired('Message is required.')])
