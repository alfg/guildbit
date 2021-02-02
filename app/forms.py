import re
from flask_wtf import FlaskForm
from wtforms import TextField, SelectField, BooleanField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Required, Email, Length, Regexp
from flask_babel import lazy_gettext as __

from app.models import Host, Package


def get_all_hosts():
    hosts = Host.get_all_hosts()

    hosts_list = []
    for host in hosts:
        hosts_list.append((host.region, host.region))
    return hosts_list

def get_active_hosts_by_type(type):
    hosts = Host.get_hosts_by_type(type)

    hosts_list = []
    for host in hosts:
        if host.active:
            hosts_list.append((host.region, host.name))
    return hosts_list

def build_packages_list():
    packages = Package.query.order_by(Package.order.desc()).all()
    packages_list = []
    for package in packages:
        packages_list.append((str(package.id), package.name))
    return packages_list


def duration_choices():
    choices = [
        ('1', '1 %s' % __('Hour')),
        ('2', '2 %s' % __('Hours')),
        ('3', '3 %s' % __('Hours')),
        ('4', '4 %s' % __('Hours'))
    ]
    return choices


class DeployServerForm(FlaskForm):
    region = SelectField('region',
                           validators=[DataRequired()],
                           choices=[])
    duration = SelectField('duration',
                           validators=[DataRequired()],
                           choices=[
                               ('1', '1 Hour'),
                               ('2', '2 Hours'),
                               ('3', '3 Hours'),
                               ('4', '4 Hours')
                           ])
    password = TextField('password',
                         validators=[DataRequired('Password is required.'),
                                     Regexp("^[A-Za-z0-9_-]*$", re.IGNORECASE, message="Password must be letters and/or numbers only."),
                                     Length(min=3, max=25,
                                            message="Password must be between 3 and 25 characters long.")])


class DeployCustomServerForm(FlaskForm):
    region = SelectField('region',
                           validators=[DataRequired()],
                           choices=[])
    slots = IntegerField('slots', default=15)
    password = TextField('password', validators=[DataRequired('Password is required.')])
    channel_name = TextField('channel_name')


class DeployTokenServerForm(FlaskForm):
    """
    Form used for creating upgraded server (premium users).
    """

    region = SelectField('region',
                           validators=[DataRequired()],
                           choices=[])
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
    email = TextField('email', validators=[Email('Invalid email address.'), DataRequired('Email is required.')])


class CreateTokenForm(FlaskForm):
    email = TextField('email')
    package = SelectField('package',
                          validators=[DataRequired()],
                          choices=[])

class CreateHostForm(FlaskForm):
    name = TextField('name', validators=[DataRequired('Name is required.')])
    hostname = TextField('hostname', validators=[DataRequired('Hostname is required.')])
    region = TextField('region', validators=[DataRequired('region is required.')])
    uri = TextField('uri', validators=[DataRequired('URI is required.')])
    username = TextField('username')
    password = TextField('password')
    type = SelectField('type',
                        validators=[DataRequired()],
                        choices=[
                            ('0', 'Free'),
                            ('1', 'Upgrade')
                        ])

class HostAdminForm(FlaskForm):
    name = TextField('name', validators=[DataRequired('Name is required.')])
    hostname = TextField('hostname', validators=[DataRequired('Hostname is required.')])
    region = TextField('region', validators=[DataRequired('region is required.')])
    uri = TextField('uri', validators=[DataRequired('URI is required.')])
    active = BooleanField('active', default=False)
    username = TextField('username')
    password = TextField('password')

class CreatePackageForm(FlaskForm):
    name = TextField('name', validators=[DataRequired('Name is required.')])
    description = TextField('description')
    price = IntegerField('price', validators=[DataRequired('Price is required.')])
    slots = IntegerField('slots', default=15)
    duration = IntegerField('duration', default=48)
    active = BooleanField('active', default=False)
    order = IntegerField('duration', default=0)

class LoginForm(FlaskForm):
    openid = TextField('openid', validators=[Required()])
    remember_me = BooleanField('remember_me', default=False)


class UserAdminForm(FlaskForm):
    role = SelectField('role',
                       validators=[DataRequired()],
                       choices=[
                           ('0', 'User'),
                           ('1', 'Admin')
                       ])


class NoticeForm(FlaskForm):
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


class SendChannelMessageForm(FlaskForm):
    _server_regions = get_all_hosts()

    message = TextField('message', validators=[DataRequired()])
    region = SelectField('region',
                           validators=[DataRequired()],
                           choices=_server_regions)


class SuperuserPasswordForm(FlaskForm):
    _server_regions = get_all_hosts()
    password = TextField('password',
                         validators=[DataRequired('Password is required.'),
                                     Length(min=3, max=25,
                                            message="Password must be between 3 and 25 characters long.")])
    region = SelectField('region',
                           validators=[DataRequired()],
                           choices=_server_regions)
    instance = IntegerField('instance')


class CleanupExpiredServersForm(FlaskForm):
    _server_regions = get_all_hosts()
    region = SelectField('region',
                           validators=[DataRequired()],
                           choices=_server_regions)


class ContactForm(FlaskForm):
    subject = TextField('subject', validators=[DataRequired('Subject is required.')])
    email = TextField('email', validators=[Email('Invalid email address.'), DataRequired('Email is required.')])
    message = TextAreaField('message', validators=[DataRequired('Message is required.')])
