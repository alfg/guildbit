import uuid

from flask import render_template, request, redirect, session, url_for, jsonify, g, flash
from flask.ext.classy import FlaskView, route
from flask.ext.login import login_user, logout_user, current_user, login_required
from flask.ext.mail import Message
import requests
import psutil

import settings
from util import admin_required
from app import app, db, tasks, lm, oid, mail, cache
from app.forms import DeployServerForm, LoginForm, UserAdminForm, DeployCustomServerForm, ContactForm, NoticeForm
from app.models import Server, User, Notice, ROLE_ADMIN, ROLE_USER


@lm.user_loader
def load_user(id):
    """
    Required user loader for flask-login
    """
    return User.query.get(int(id))


@app.before_request
def before_request():
    """
    Required user loader for flask-login
    """
    g.user = current_user


@app.context_processor
@cache.cached(timeout=100, key_prefix='display_notice')
def display_notice():
    """
    Context processor for displaying a notice (if enabled) on the base template header area
    """
    notice = Notice.query.get(1)  # First entry is the base header notice
    return dict(notice=notice)


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

    @route('/how-it-works/')
    def how_it_works(self):
        return render_template('how_it_works.html')

    @route('/donate/')
    def donate(self):
        return render_template('donate.html')

    @route('/contact/', methods=['POST', 'GET'])
    def contact(self):
        form = ContactForm()
        if form.validate_on_submit():
            try:
                template = """
                              This is a contact form submission from Guildbit.com/contact \n
                              Email: %s \n
                              Comment/Question: %s \n
                           """ % (form.email.data, form.message.data)

                msg = Message(
                    form.subject.data,
                    sender=settings.DEFAULT_MAIL_SENDER,
                    recipients=settings.EMAIL_RECIPIENTS)

                msg.body = template
                mail.send(msg)
            except:
                import traceback
                traceback.print_exc()
                flash("Something went wrong!")
                return redirect('/contact')

            return render_template('contact_thankyou.html')
        return render_template('contact.html', form=form)

    @route('/about/')
    def about(self):
        return render_template('about.html')

    @route('/terms/')
    def terms(self):
        return render_template('terms.html')

    @route('/privacy/')
    def privacy(self):
        return render_template('privacy.html')


class ServerView(FlaskView):

    def index(self):
        return redirect(url_for('home'))

    def get(self, id):
        server = Server.query.filter_by(uuid=id).first_or_404()
        r = requests.get("%s/api/v1/servers/%i" % (settings.MURMUR_REST_HOST, server.mumble_instance))
        if r.status_code == 200:
            server_details = r.json()
            return render_template('server.html', server=server, details=server_details)
        else:
            return render_template('server_expired.html', server=server)

    @route('/<id>/users/')
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
        stats = requests.get("%s/api/v1/stats/" % settings.MURMUR_REST_HOST)
        users_count = User.query.count()
        servers_count = Server.query.count()
        ps = psutil

        ctx = {
            'servers_online': stats.json()['booted_servers'],
            'users_online': stats.json()['users_online'],
            'users': users_count,
            'servers': servers_count,
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
        form = DeployCustomServerForm()
        filter = request.args.get('filter')
        stats = requests.get("%s/api/v1/stats/" % settings.MURMUR_REST_HOST)
        stats_ctx = {
            'servers_online': stats.json()['booted_servers'],
            'users_online': stats.json()['users_online']
        }

        if filter == "all":
            servers = Server.query.order_by(Server.id.desc()).all()
        elif filter == "active":
            servers = Server.query.filter_by(status="active").order_by(Server.id.desc()).all()
        elif filter == "expired":
            servers = Server.query.filter_by(status="expired").order_by(Server.id.desc()).all()
        elif filter == "custom":
            servers = Server.query.filter_by(type="custom").order_by(Server.id.desc()).all()
        else:
            servers = Server.query.filter_by(status="active").order_by(Server.id.desc()).all()

        return render_template('admin/servers.html', servers=servers, form=form, stats=stats_ctx, title="Servers")

    @login_required
    @admin_required
    def get(self, id):
        server = Server.query.filter_by(id=id).first_or_404()
        r = requests.get("%s/api/v1/servers/%i" % (settings.MURMUR_REST_HOST, server.mumble_instance))
        if r.status_code == 200:
            server_details = r.json()
        else:
            server_details = None

        return render_template('admin/server.html', server=server, details=server_details, title="Server: %s" % id)

    @login_required
    @admin_required
    def post(self):
        form = DeployCustomServerForm()
        if form.validate_on_submit():

            try:
                # Generate UUID
                gen_uuid = str(uuid.uuid4())

                # Create POST request to murmur-rest api to create a new server
                welcome_msg = "Welcome. This is a custom GuildBit Mumble instance. View details on this server by " \
                              "<a href='http://guildbit.com/server/%s'>clicking here.</a>" % gen_uuid
                payload = {
                    'password': form.password.data,
                    'welcometext': welcome_msg,
                    'users': form.slots.data or 0,
                    'registername': form.channel_name
                }
                r = requests.post(settings.MURMUR_REST_HOST + "/api/v1/servers/", data=payload)
                server_id = r.json()['id']

                # Create database entry
                s = Server()
                s.duration = 0
                s.password = form.password.data
                s.uuid = gen_uuid
                s.mumble_instance = server_id
                s.type = 'custom'
                db.session.add(s)
                db.session.commit()

                return redirect('/admin/servers/%s' % s.id)

            except:
                import traceback
                db.session.rollback()
                traceback.print_exc()

            return render_template('admin/server.html', form=form)
        return render_template('admin/server.html', form=form)

    @login_required
    @admin_required
    @route('/<id>/kill', methods=['POST'])
    def kill_server(self, id):
        server = Server.query.filter_by(id=id).first_or_404()
        server.status = "expired"
        db.session.commit()
        r = requests.delete("%s/api/v1/servers/%i" % (settings.MURMUR_REST_HOST, server.mumble_instance))
        return redirect('/admin/servers/%s' % id)


class AdminUsersView(FlaskView):

    @login_required
    @admin_required
    def index(self):
        users = User.query.all()
        return render_template('admin/users.html', users=users, title="Users")

    @login_required
    @admin_required
    def get(self, id):
        user = User.query.filter_by(id=id).first_or_404()
        form = UserAdminForm(role=user.role)
        return render_template('admin/user.html', u=user, form=form, title="User: %s" % user.nickname)

    @login_required
    @admin_required
    def post(self, id):
        user = User.query.filter_by(id=id).first()
        form = UserAdminForm(request.form, role=user.role)
        if form.validate_on_submit():
            user.role = form.role.data
            db.session.commit()
            return redirect('/admin/users/%s' % user.id)
        return render_template('admin/user.html', u=user, form=form, title="User: %s" % user.nickname)


class AdminHostsView(FlaskView):

    @login_required
    @admin_required
    def index(self):
        hosts = settings.MURMUR_HOSTS

        ctx = []
        for i in hosts:
            r = requests.get("%s/api/v1/stats/" % settings.MURMUR_REST_HOST)
            ctx.append({
                'name': i['name'],
                'address': i['address'],
                'contact': i['contact'],
                'status': i['status'],
                'booted_servers': r.json()['booted_servers'],
                'capacity': i['capacity']
            })

        return render_template('admin/hosts.html', hosts=ctx, title="Hosts")


class AdminToolsView(FlaskView):

    @login_required
    @admin_required
    def index(self):
        notice = Notice.query.filter_by(location='base').first()
        notice_form = NoticeForm(obj=notice)
        return render_template('admin/tools.html', notice_form=notice_form, title="Tools")

    @login_required
    @admin_required
    @route('/header-message', methods=['POST'])
    def update_header_message(self):
        notice = Notice.query.filter_by(location='base').first()
        form = NoticeForm(obj=notice)
        if form.validate_on_submit():

            if notice is None:
                notice = Notice(form.message_type.data, form.message.data, 'base')
            else:
                notice.active = form.active.data
                notice.message_type = form.message_type.data
                notice.message = form.message.data
                notice.location = 'base'

            db.session.add(notice)
            db.session.commit()
            return redirect('/admin/tools/')
        return redirect('/admin/tools/')


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


@app.errorhandler(404)
def page_not_found(error):
    return render_template('_error_pages/404.html'), 404


@app.errorhandler(500)
def page_not_found(error):
    return render_template('_error_pages/500.html'), 500


# Register views
HomeView.register(app, route_base='/')
ServerView.register(app)
AdminView.register(app)
AdminServersView.register(app, route_prefix='/admin/', route_base='/servers')
AdminUsersView.register(app, route_prefix='/admin/', route_base='/users')
AdminHostsView.register(app, route_prefix='/admin/', route_base='/hosts')
AdminToolsView.register(app, route_prefix='/admin/', route_base='/tools')
