import uuid

from flask import Flask
from flask import render_template, redirect, url_for, jsonify

from flask.ext.classy import FlaskView, route

from forms import DeployServerForm
from models import *

import requests

import config

app = Flask(__name__)
app.secret_key = 'testkey'


class HomeView(FlaskView):

    def index(self):
        form = DeployServerForm()
        return render_template('index.html', form=form)

    def post(self):
        form = DeployServerForm()
        if form.validate_on_submit():

            try:
                r = requests.post("http://localhost:5000/api/v1/servers/")

                s = Server()
                s.duration = form.duration.data
                s.password = form.password.data
                s.uuid = str(uuid.uuid4())
                s.mumble_instance = r.json()['server']['id']
                db.session.add(s)
                db.session.commit()
                return redirect(url_for('ServerView:get', id=s.uuid))

            except:
                import traceback
                db.session.rollback()
                traceback.print_exc()

            return render_template('index.html', form=form)
        return render_template('index.html', form=form)

    @route('/how-it-works')
    def how_it_works(self):
        return render_template('how_it_works.html')

    @route('/donate')
    def donate(self):
        return render_template('donate.html')

    @route('/about')
    def about(self):
        return render_template('about.html')

    @route('/terms')
    def terms(self):
        return render_template('terms.html')

    @route('/privacy')
    def privacy(self):
        return render_template('privacy.html')


class ServerView(FlaskView):

    def index(self):
        return render_template('server.html')

    def get(self, id):
        server = Server.query.filter_by(uuid=id).first_or_404()
        r = requests.get("http://localhost:5000/api/v1/servers/%i" % server.mumble_instance)
        server_details = r.json()
        return render_template('server.html', server=server, details=server_details)

    @route('/<id>/users')
    def users(self, id):
        server = Server.query.filter_by(uuid=id).first_or_404()
        r = requests.get("http://localhost:5000/api/v1/servers/%i" % server.mumble_instance)
        user_details = r.json()
        users = {
            'count': user_details['server']['users'],
            'users': user_details['server']['tree']['users']
        }
        return jsonify(users=users)



HomeView.register(app, route_base='/')
ServerView.register(app)

if __name__ == '__main__':
    app.run(debug=config.APP_DEBUG, host=config.APP_HOST, port=config.APP_PORT)
