import uuid

from flask import render_template, request, redirect, session, url_for, jsonify, g, flash
from flask.ext.classy import FlaskView, route
from flask.ext.login import login_user, logout_user, current_user, login_required
import requests
import psutil

import settings
from util import admin_required
from app import app, db, tasks, lm, oid
from app.forms import DeployServerForm, LoginForm
from app.models import Server, User, ROLE_ADMIN, ROLE_USER


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.before_request
def before_request():
    g.user = current_user


class HomeView(FlaskView):

    @route('/', endpoint='home')
    def index(self):
        user = g.user
        form = DeployServerForm()
        return render_template('index.html', form=form)

    def post(self):
        form = DeployServerForm()
        if form.validate_on_submit():

            try:
                # Generate UUID
                gen_uuid = str(uuid.uuid4())

                # Create POST request to murmur-rest api to create a new server
                welcome_msg = "Welcome. This is a temporary GuildBit Mumble instance. View details on this server by " \
                              "<a href='http://guildbit.com/server/%s'>clicking here.</a>" % gen_uuid
                payload = {
                    'password': form.password.data,
                    'welcometext': welcome_msg,
                    'users': settings.DEFAULT_MAX_USERS,
                    'registername': settings.DEFAULT_CHANNEL_NAME
                }
                r = requests.post(settings.MURMUR_REST_HOST + "/api/v1/servers/", data=payload)
                server_id = r.json()['id']

                # Create database entry
                s = Server()
                s.duration = form.duration.data
                s.password = form.password.data
                s.uuid = gen_uuid
                s.mumble_instance = server_id
                db.session.add(s)
                db.session.commit()

                # Send task to delete server on expiration
                tasks.delete_server.apply_async([server_id, gen_uuid], eta=s.expiration)
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
            return render_template('server.html', server=server, details=server_details)
        else:
            return render_template('server_expired.html', server=server)

    @route('/<id>/users')
    def users(self, id):
        server = Server.query.filter_by(uuid=id).first_or_404()
        r = requests.get("%s/api/v1/servers/%i" % (settings.MURMUR_REST_HOST, server.mumble_instance))
        if r.status_code == 200:
            user_details = r.json()
            users = {
                'count': user_details['user_count'],
                'users': user_details['users']
            }
            return jsonify(users=users)
        else:
            return jsonify(users=None)


class AdminView(FlaskView):
    """
    All base admin views.
    """

    @login_required
    @admin_required
    def index(self):

        servers_running = requests.get("%s/api/v1/servers/" % settings.MURMUR_REST_HOST)
        users_count = User.query.count()
        ps = psutil
        print ps.virtual_memory()

        ctx = {
            'servers_count': len(servers_running.json()),
            'users_count': users_count,
            'memory': ps.virtual_memory(),
            'disk': ps.disk_usage('/')
        }
        return render_template('admin/dashboard.html', title="Dashboard", ctx=ctx)


class AdminServersView(FlaskView):
    """
    Admin Server view.
    """

    @login_required
    @admin_required
    def index(self):

        filter = request.args.get('filter')

        if filter == "all":
            servers = Server.query.all()
        elif filter == "active":
            servers = Server.query.filter_by(status="active").all()
        elif filter == "expired":
            servers = Server.query.filter_by(status="expired").all()
        else:
            servers = Server.query.filter_by(status="active").all()

        return render_template('admin/servers.html', servers=servers, title="Servers")

    @login_required
    @admin_required
    def get(self, id):

        server = Server.query.filter_by(id=id).first_or_404()
        r = requests.get("%s/api/v1/servers/%i" % (settings.MURMUR_REST_HOST, server.mumble_instance))
        server_details = r.json()
        return render_template('admin/server.html', server=server, details=server_details, title="Server: %s" % id)


class AdminUsersView(FlaskView):

    @login_required
    @admin_required
    def index(self):

        users = User.query.all()
        return render_template('admin/users.html', users=users, title="Users")


@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('home'))

    form = LoginForm()
    if form.validate_on_submit():
        session['remember_me'] = form.remember_me.data
        return oid.try_login(form.openid.data, ask_for=['nickname', 'email'], ask_for_optional=['fullname'])
    return render_template('auth/login.html',
                           title='Sign In',
                           form=form,
                           providers=settings.OPENID_PROVIDERS)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@oid.after_login
def after_login(resp):
    if resp.email is None or resp.email == "":
        flash('Invalid login. Please try again.')
        return redirect(url_for('login'))
    user = User.query.filter_by(email=resp.email).first()
    if user is None:
        nickname = resp.nickname
        if nickname is None or nickname == "":
            nickname = resp.email.split('@')[0]
        user = User(nickname=nickname, email=resp.email, role=ROLE_USER)
        db.session.add(user)
        db.session.commit()
    remember_me = False
    if 'remember_me' in session:
        remember_me = session['remember_me']
        session.pop('remember_me', None)
    login_user(user, remember=remember_me)
    return redirect(request.args.get('next') or url_for('home'))


# Register views
HomeView.register(app, route_base='/')
ServerView.register(app)
AdminView.register(app)
AdminServersView.register(app, route_prefix='/admin/', route_base='/servers')
AdminUsersView.register(app, route_prefix='/admin/', route_base='/users')

