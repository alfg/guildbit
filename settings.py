APP_HOST = '0.0.0.0'
APP_PORT = 4000
APP_DEBUG = True
APP_SESSION_KEY = 'testsession'
DATABASE_URI = 'sqlite:////tmp/test.db'
BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
MURMUR_REST_HOST = 'http://localhost:5000'

DEFAULT_MAX_USERS = 10