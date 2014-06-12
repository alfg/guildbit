# -*- coding: utf-8 -*-

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
CACHE_BACKEND = 'redis'

# Murmur default settings
DEFAULT_MAX_USERS = 10
DEFAULT_CHANNEL_NAME = 'GuildBit.com Mumble Server'
DEFAULT_MURMUR_PORT = 50000  # Murmur server port

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
    {'name': 'Yahoo', 'url': 'https://me.yahoo.com'}
]

LANGUAGES = {
    'en': 'English',
    'es': 'Español'
}

MURMUR_HOSTS = [
    {
        'name': 'localhost',
        'address': 'localhost:5000',
        'uri': 'http://localhost:5000',
        'hostname': 'localhost',
        'http_uri': 'http://localhost:4000/static/img',
        'monitor_uri': 'http://localhost:5555',
        'contact': 'alf.g.jr@gmail.com',
        'location': 'local',
        'location_name': 'Local',
        'status': 'active',
        'capacity': 100,
        'username': '',
        'password': ''
    }
]

PACKAGES = [
    {
        'name': 'PACKAGE-Test',
        'slots': 10,
        'duration': 48  # Days in hours
    },
    {
        'name': 'PACKAGE-A',
        'slots': 25,
        'duration': 168  # Days in hours
    },
    {
        'name': 'PACKAGE-B',
        'slots': 25,
        'duration': 336  # Days in hours
    },
    {
        'name': 'PACKAGE-C',
        'slots': 25,
        'duration': 720 # Days in hours
    }
]
