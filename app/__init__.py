from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
import settings

app = Flask(__name__)
app.secret_key = settings.APP_SESSION_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URI
db = SQLAlchemy(app)

from app import views

db.create_all()
