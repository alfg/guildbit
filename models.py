import datetime
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.ext.hybrid import hybrid_property


from guildbit import app
import settings

app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URI
db = SQLAlchemy(app)


class Server(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String, unique=True, index=True)
    created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow())
    duration = db.Column(db.Integer)
    password = db.Column(db.String)
    mumble_instance = db.Column(db.Integer)

    @hybrid_property
    def expiration(self):
        return self.created_date + datetime.timedelta(hours=self.duration)

    def __repr__(self):
        return '<Server %r>' % self.id
