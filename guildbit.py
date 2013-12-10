import uuid

from flask import Flask
from flask import render_template, redirect, url_for, jsonify
from flask.ext.classy import FlaskView, route
import requests

from forms import DeployServerForm
from models import *
import settings
import tasks

app = Flask(__name__)
app.secret_key = settings.APP_SESSION_KEY


class HomeView(FlaskView):

    def index(self):
        form = DeployServerForm()
        return render_template('index.html', form=form)

    def post(self):
        form = DeployServerForm()
        if form.validate_on_submit():

            try:
                gen_uuid = str(uuid.uuid4())
                # Create POST request to murmur-rest api to create a new server
                welcome_msg = "Welcome. This is a temporary GuildBit Mumble instance. View details on this server by " \
                              "<a href='http://guildbit.com/server/%s'>clicking here.</a>" % gen_uuid
                payload = {'password': form.password.data, 'welcometext': welcome_msg}
                r = requests.post(settings.MURMUR_REST_HOST + "/api/v1/servers/", data=payload)
                server_id = r.json()['server']['id']

                # Create database entry
                s = Server()
                s.duration = form.duration.data
                s.password = form.password.data
                s.uuid = gen_uuid
                s.mumble_instance = server_id
                db.session.add(s)
                db.session.commit()

                # Send task to delete server on expiration
                tasks.delete_server.apply_async([server_id], eta=s.expiration)
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
        r = requests.get("%s/api/v1/servers/%i" % (settings.MURMUR_REST_HOST, server.mumble_instance))
        if r.status_code == 200:
            server_details = r.json()
        else:
            return render_template('server_expired.html', server=server)
        return render_template('server.html', server=server, details=server_details)

    @route('/<id>/users')
    def users(self, id):
        server = Server.query.filter_by(uuid=id).first_or_404()
        r = requests.get("%s/api/v1/servers/%i" % (settings.MURMUR_REST_HOST, server.mumble_instance))
        user_details = r.json()
        users = {
            'count': user_details['server']['users'],
            'users': user_details['server']['tree']['users']
        }
        return jsonify(users=users)



HomeView.register(app, route_base='/')
ServerView.register(app)

if __name__ == '__main__':
    app.run(debug=settings.APP_DEBUG, host=settings.APP_HOST, port=settings.APP_PORT)
