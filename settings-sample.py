import os

APP_HOST = '0.0.0.0'
APP_PORT = 4000
APP_DEBUG = True
APP_SESSION_KEY = 'super-secret'
CSRF_ENABLED = True
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

DATABASE_URI = 'sqlite:////tmp/test.db'
BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
MURMUR_REST_HOST = 'http://localhost:5000'

DEFAULT_MAX_USERS = 10
DEFAULT_CHANNEL_NAME = 'GuildBit.com Mumble Server'

MAIL_SERVER = 'email-smtp.us-east-1.amazonaws.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USE_SSL = True
MAIL_USERNAME = ''
MAIL_PASSWORD = ''
DEFAULT_MAIL_SENDER = 'alf.g.jr@gmail.com'
EMAIL_RECIPIENTS = ['alf.g.jr@gmail.com']

OPENID_PROVIDERS = [
    {'name': 'Google', 'url': 'https://www.google.com/accounts/o8/id'},
    {'name': 'Yahoo', 'url': 'https://me.yahoo.com'}]

MURMUR_HOSTS = [
    {
        'name': 'GuildBit',
        'address': 'localhost:5000',
        'uri': 'http://localhost:5000',
        'contact': 'alf.g.jr@gmail.com',
        'status': 'active',
        'capacity': 100,
    }
]
