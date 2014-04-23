import os
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.openid import OpenID
from flask.ext.mail import Mail
from flask.ext.cache import Cache
from flask.ext.babel import Babel

import settings

app = Flask(__name__)
app.secret_key = settings.APP_SESSION_KEY

# Configure Flask-login
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'
oid = OpenID(app, os.path.join(settings.BASE_DIR, 'tmp'))

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URI
db = SQLAlchemy(app)

# Configure Flask-Mail
app.config['MAIL_SERVER'] = settings.MAIL_SERVER
app.config['MAIL_PORT'] = settings.MAIL_PORT
app.config['MAIL_USE_TLS'] = settings.MAIL_USE_TLS
app.config['MAIL_USERNAME'] = settings.MAIL_USERNAME
app.config['MAIL_PASSWORD'] = settings.MAIL_PASSWORD
mail = Mail(app)

# Configure Flask-Cache
app.config['CACHE_TYPE'] = settings.CACHE_BACKEND
cache = Cache(app)

# Configure Babel
babel = Babel(app)

# Configure email error handler
if not app.debug:
    ADMINS = settings.EMAIL_RECIPIENTS
    import logging
    from logging.handlers import SMTPHandler
    mail_handler = SMTPHandler('localhost', 'server-error@guildbit.com', ADMINS, 'Guildbit Exception')
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)

# Configure rotating file logging
if not app.debug:
    import logging
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler('tmp/guildbit.log', 'a', 1 * 1024 * 1024, 10)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('guildbit startup')

from app import views

db.create_all()

