import datetime
from sqlalchemy.ext.hybrid import hybrid_property

from app import db

ROLE_USER = 0
ROLE_ADMIN = 1


class Server(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String, unique=True, index=True)
    created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    duration = db.Column(db.Integer)
    password = db.Column(db.String)
    status = db.Column(db.String, default='active')
    mumble_host = db.Column(db.String, default="mumble.guildbit.com")
    mumble_instance = db.Column(db.Integer)

    @hybrid_property
    def expiration(self):
        return self.created_date + datetime.timedelta(hours=self.duration)

    def __repr__(self):
        return '<Server %r>' % self.id


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(64), unique=True)
    email = db.Column(db.String(120), unique=True)
    role = db.Column(db.SmallInteger, default=ROLE_USER)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return '<User %r>' % self.nickname