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

    def get_role(self):
        return self.role

    def get_role_name(self):
        if self.role == 0:
            role_name = "user"
        elif self.role == 1:
            role_name = "admin"
        else:
            role_name = "unassigned"
        return role_name

    def __repr__(self):
        return '<User %r>' % self.nickname


class Host(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hostname = db.Column(db.String(120), unique=True, index=True)
    status = db.Column(db.String, default='active')
    contact_name = db.Column(db.String(120))
    contact_email = db.Column(db.String(120))
    created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return '<Host %r>' % self.hostname

