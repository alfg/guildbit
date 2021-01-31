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
DATABASE_URI = 'postgresql://postgres:postgres@db:5432/guildbit'
BROKER_URL = 'redis://%s/0' % REDIS_HOST
CELERY_RESULT_BACKEND = 'redis://%s/0' % REDIS_HOST
CACHE_BACKEND = 'redis'
CACHE_REDIS_URL = 'redis://%s/2' % REDIS_HOST

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
DEFAULT_MAIL_SENDER = 'no-reply@guildbit.com'
EMAIL_RECIPIENTS = ['alf.g.jr@gmail.com']

OPENID_PROVIDERS = [
    {'name': 'Steam', 'url': 'http://steamcommunity.com/openid'}
]

STEAM_API_KEY = 'XXXXXX'

LANGUAGES = {
    'en': 'English',
    'fr': 'français',
    'sw': 'Kiswahili'
}