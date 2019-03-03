import os
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager, Server
from flask_migrate import Migrate, MigrateCommand
from flask_login import LoginManager
from flask_openid import OpenID
from flask_mail import Mail
from flask_cache import Cache
from flask_babel import Babel
from flask_assets import Environment, Bundle

import settings

app = Flask(__name__)
app.secret_key = settings.APP_SESSION_KEY

# Version
app.config.version = '1.4.0'
app.config.last_updated = datetime.now()

# Configure Flask-login
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'
oid = OpenID(app, os.path.join(settings.BASE_DIR, 'tmp'))

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URI
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Configure Flask-Script
manager = Manager(app)
manager.add_command('runserver', Server(host=settings.APP_HOST, port=settings.APP_PORT))
manager.add_command('db', MigrateCommand)

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


# Configure Flask-Assets
assets = Environment(app)
app.config['ASSETS_DEBUG'] = settings.ASSETS_DEBUG

js = Bundle('js/libs/tooltips.min.js', 'js/main.js', 'js/libs/jquery.fancybox.js',
            'js/libs/modal.js',
            filters='jsmin', output='gen/packed.js')
css = Bundle('css/pure-min.css', 'css/grids-responsive-min.css', 'css/style.css', 'css/tooltips.css',
             'css/jquery.fancybox.css', 'css/modals.css',
             filters='cssmin', output='gen/packed.css')
assets.register('js_all', js)
assets.register('css_all', css)

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
    file_handler = RotatingFileHandler('/tmp/guildbit.log', 'a', 1 * 1024 * 1024, 10)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('guildbit startup')

from app import views

db.create_all()
