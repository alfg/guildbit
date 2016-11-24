# -*- coding: utf-8 -*-

import os

APP_HOST = '0.0.0.0'
APP_PORT = 5000
APP_DEBUG = True
APP_SESSION_KEY = 'super-secret'
CSRF_ENABLED = True
ASSETS_DEBUG = True
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost:6379')
DATABASE_URI = 'sqlite:////tmp/test.db'
BROKER_URL = 'redis://%s/0' % REDIS_HOST
CELERY_RESULT_BACKEND = 'redis://%s/0' % REDIS_HOST
CACHE_BACKEND = 'simple'

# Murmur default settings
DEFAULT_MAX_USERS = 15
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
    {'name': 'Steam', 'url': 'http://steamcommunity.com/openid'}
]

STEAM_API_KEY = 'XXXXXX'

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

# Use only if in test docker environment.
DOCKER_TEST = os.environ.get('DOCKER_TEST', False)
if DOCKER_TEST:
    MURMUR_HOSTS = [{
        'name': 'Test Server',
        'address': 'murmur-rest:5000',
        'uri': 'http://murmur-rest:5000',
        'hostname': 'murmur-rest',
        'http_uri': 'http://localhost:4000/static/img',
        'monitor_uri': 'http://localhost:5555',
        'location': 'local',
        'location_name': 'Local',
        'status': 'active',
        'capacity': 100,
        'username': '',
        'password': ''
    }]

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
