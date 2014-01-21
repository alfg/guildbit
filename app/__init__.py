from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager

import settings

app = Flask(__name__)
app.secret_key = settings.APP_SESSION_KEY
lm = LoginManager()
lm.init_app(app)
app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URI
db = SQLAlchemy(app)

from app import views

db.create_all()
