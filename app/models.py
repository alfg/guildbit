import datetime
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func

from app import db

# User roles.
ROLE_USER = 0
ROLE_ADMIN = 1

# Host types.
HOST_TYPE_FREE = 0
HOST_TYPE_UPGRADE = 1


class Server(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String, unique=True, index=True)
    created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    duration = db.Column(db.Integer)
    password = db.Column(db.String)
    status = db.Column(db.String, default='queued')
    type = db.Column(db.String, default='temp')
    mumble_host = db.Column(db.String, default="mumble.guildbit.com")
    mumble_instance = db.Column(db.Integer)
    cvp_uuid = db.Column(db.String, unique=True, index=True, default=None)
    ip = db.Column(db.String(64))
    extensions = db.Column(db.SmallInteger, default=0)

    ratings = db.relationship('Rating', backref='server', lazy='dynamic')

    @hybrid_property
    def expiration(self):
        return self.created_date + datetime.timedelta(hours=self.duration)

    @hybrid_property
    def is_expired(self):
        now = datetime.datetime.utcnow()
        exp = self.created_date + datetime.timedelta(hours=self.duration)
        return now > exp

    def __repr__(self):
        return '<Server %r>' % self.id


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    steam_id = db.Column(db.String(40), unique=True)
    nickname = db.Column(db.String(64), unique=True)
    email = db.Column(db.String(120), unique=True)
    role = db.Column(db.SmallInteger, default=ROLE_USER)
    created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)

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
        if self.role == ROLE_USER:
            role_name = "user"
        elif self.role == ROLE_ADMIN:
            role_name = "admin"
        else:
            role_name = "unassigned"
        return role_name

    @staticmethod
    def get_or_create(steam_id):
        rv = User.query.filter_by(steam_id=steam_id).first()
        if rv is None:
            rv = User()
            rv.steam_id = steam_id
            db.session.add(rv)
        return rv

    def __repr__(self):
        return '<User %r>' % self.nickname


class Notice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column(db.Boolean, default=False)
    created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    message_type = db.Column(db.String(120), index=True)
    message = db.Column(db.String)
    location = db.Column(db.String(120), index=True, unique=True)

    def __init__(self, message_type, message, location):
        self.message_type = message_type
        self.message = message
        self.location = location

    def __repr__(self):
        return '<Notice %r>' % self.id


class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    server_uuid = db.Column(db.String, db.ForeignKey('server.uuid'), index=True)
    created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    ip = db.Column(db.String(64))
    stars = db.Column(db.Integer)
    feedback = db.Column(db.String())

    @staticmethod
    def get_rating_average():
        avg = Rating.query.with_entities(func.avg(Rating.stars).label('avg')).scalar() or 0
        return round(avg, 2)

    def __repr__(self):
        return '<Rating %r>' % self.id


class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String, unique=True, index=True)
    created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    activation_date = db.Column(db.DateTime)
    active = db.Column(db.Boolean, default=True)
    email = db.Column(db.String(120))
    package = db.Column(db.String(32))
    package_id = db.Column(db.Integer, db.ForeignKey('package.id'), index=True)

    @hybrid_property
    def get_package_name(self):
        package = Package.query.filter_by(id=self.package_id).first()
        return package.name

    def __repr__(self):
        return '<Token %r>' % self.id


class Host(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=False, index=True)
    hostname = db.Column(db.String(120), unique=True, index=True)
    region = db.Column(db.String(120), unique=True, index=True)
    uri = db.Column(db.String(120), unique=False, index=False)
    active = db.Column(db.Boolean, default=False)
    type = db.Column(db.SmallInteger, default=HOST_TYPE_FREE)
    username = db.Column(db.String(120), unique=False, index=False)
    password = db.Column(db.String(120), unique=False, index=False)

    def get_host_type(self):
        if self.role == HOST_TYPE_FREE:
            role_name = "free"
        elif self.role == HOST_TYPE_UPGRADE:
            role_name = "upgrade"
        else:
            role_name = "unassigned"
        return role_name

    @staticmethod
    def get_hosts_by_type(type):
        if type == "free":
            type = HOST_TYPE_FREE
        elif type == "upgrade":
            type = HOST_TYPE_UPGRADE
        hosts = Host.query.filter_by(type=type).all()
        return hosts

    @staticmethod
    def get_all_hosts():
        hosts = Host.query.all()
        return hosts

    def __repr__(self):
        return '<Host %r>' % self.hostname


class Package(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=False, index=True)
    description = db.Column(db.String)
    price = db.Column(db.Integer)
    slots = db.Column(db.Integer)
    duration = db.Column(db.Integer)
    active = db.Column(db.Boolean, default=False)
    order = db.Column(db.Integer, default=0)