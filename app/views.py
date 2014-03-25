import uuid

from flask import render_template, request, redirect, session, url_for, jsonify, g, flash
from flask.ext.classy import FlaskView, route
from flask.ext.login import login_user, logout_user, current_user, login_required
from flask.ext.mail import Message
import psutil

import settings
from util import admin_required
from app import app, db, tasks, lm, oid, mail, cache
from app.forms import DeployServerForm, LoginForm, UserAdminForm, DeployCustomServerForm, ContactForm, NoticeForm
from app.forms import SendChannelMessageForm, LeaveFeedbackForm, build_hosts_list
from app.models import Server, User, Notice, Rating, ROLE_USER
import app.murmur as murmur


## Flask-Login required user loaders
@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


## Request processing
@app.before_request
def before_request():
    g.user = current_user  # Required for flask-login


## Context processors
@app.context_processor
@cache.cached(timeout=100, key_prefix='display_notice')
def display_notice():
    """
    Context processor for displaying a notice (if enabled) on the base template header area
    """
    notice = Notice.query.get(1)  # First entry is the base header notice
    return dict(notice=notice)


## Home views
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

                server_id = murmur.create_server_by_location(form.location.data, payload)

                # Create database entry
                s = Server()
                s.duration = form.duration.data
                s.password = form.password.data
                s.uuid = gen_uuid
                s.mumble_instance = server_id
                s.mumble_host = murmur.get_murmur_hostname(form.location.data)
                db.session.add(s)
                db.session.commit()

                # Send task to delete server on expiration
                tasks.delete_server.apply_async([gen_uuid], eta=s.expiration)
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

    @route('/updates/')
    def updates(self):
        return render_template('updates.html')


## Server views
class ServerView(FlaskView):

    def index(self):
        return redirect(url_for('home'))

    def get(self, id):
        ip = request.remote_addr
        server = Server.query.filter_by(uuid=id).first_or_404()
        rating = Rating.query.filter_by(server_id=id, ip=ip).first()

        server_details = murmur.get_server(server.mumble_host, server.mumble_instance)
        if server_details is not None:
            return render_template('server.html', server=server, details=server_details, rating=rating)
        else:
            return render_template('server_expired.html', server=server)

    @route('/<id>/users/')
    def users(self, id):
        server = Server.query.filter_by(uuid=id).first_or_404()
        server_details = murmur.get_server(server.mumble_host, server.mumble_instance)
        if server_details is not None:
            users = {
                'count': server_details['user_count'],
                'users': server_details['users']
            }
            return jsonify(users=users)
        else:
            return jsonify(users=None)

    @route('/<id>/rating', methods=['POST'])
    def rating(self, id):
        ip = request.remote_addr
        stars = request.form['stars']

        r = Rating.query.filter_by(server_id=id, ip=ip).first()
        print r

        if r is None:
            try:
                r = Rating()
                r.server_id = id
                r.ip = ip
                r.stars = stars
                db.session.add(r)
                db.session.commit()
            except:
                import traceback
                db.session.rollback()
                traceback.print_exc()

            return jsonify(message='success')
        else:
            r.stars = stars
            db.session.commit()

        return jsonify(message=r.stars)

    @route('/<id>/feedback', methods=['POST'])
    def feedback(self, id):
        ip = request.remote_addr
        feedback = request.form['feedback']

        if feedback:
            try:
                r = Rating.query.filter_by(server_id=id, ip=ip).first()
                r.feedback = feedback
                db.session.commit()
            except:
                import traceback
                db.session.rollback()
                traceback.print_exc()

            return jsonify(message='success')

        return jsonify(message='error')


## Admin views
class AdminView(FlaskView):
    """
    All base admin views.
    """

    @login_required
    @admin_required
    def index(self):
        filter = request.args.get('filter')
        stats = murmur.get_all_server_stats()
        users_count = User.query.count()
        servers_count = Server.query.count()
        ps = psutil

        server_list = build_hosts_list()
        if filter is not None:
            http_uri = murmur.get_http_uri(filter)
        else:
            http_uri = murmur.get_http_uri(server_list[0][0])

        ctx = {
            'servers_online': stats['servers_online'],
            'users_online': stats['users_online'],
            'users': users_count,
            'servers': servers_count,
            'memory': ps.virtual_memory(),
            'disk': ps.disk_usage('/'),
            'http_uri': http_uri
        }
        return render_template('admin/dashboard.html', title="Dashboard", ctx=ctx, server_list=server_list)


class AdminServersView(FlaskView):
    """
    Admin Server view.
    """

    @login_required
    @admin_required
    def index(self):
        form = DeployCustomServerForm()
        filter = request.args.get('filter')
        stats = murmur.get_all_server_stats()
        stats_ctx = {
            'servers_online': stats.get('servers_online'),
            'users_online': stats.get('users_online')
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
        server_details = murmur.get_server(server.mumble_host, server.mumble_instance)

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
                    'users': form.slots.data,
                    'registername': form.channel_name.data
                }
                server_id = murmur.create_server_by_location(form.location.data, payload)

                # Create database entry
                s = Server()
                s.mumble_host = murmur.get_murmur_hostname(form.location.data)
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

        try:
            murmur.delete_server(server.mumble_host, server.mumble_instance)
            server.status = "expired"
            db.session.commit()
        except:
            import traceback
            db.session.rollback()
            traceback.print_exc()

        return redirect('/admin/servers/%s' % id)

    @login_required
    @admin_required
    @route('/<id>/logs', methods=['GET'])
    def server_log(self, id):
        server = Server.query.filter_by(id=id).first_or_404()
        logs = murmur.get_server_logs(server.mumble_host, server.mumble_instance)
        return jsonify(logs=logs)


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
            r = murmur.get_server_stats(i['hostname'])

            ctx.append({
                'name': i['name'],
                'address': i['address'],
                'contact': i['contact'],
                'status': i['status'],
                'booted_servers': r.get('servers_online', 0),
                'capacity': i['capacity'],
                'monitor_url': i['monitor_uri']
            })

        return render_template('admin/hosts.html', hosts=ctx, title="Hosts")


class AdminToolsView(FlaskView):

    @login_required
    @admin_required
    def index(self):
        notice = Notice.query.filter_by(location='base').first()
        notice_form = NoticeForm(obj=notice)
        message_form = SendChannelMessageForm()
        return render_template('admin/tools.html', notice_form=notice_form, message_form=message_form, title="Tools")

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

    @login_required
    @admin_required
    @route('/send-channel-message', methods=['POST'])
    def send_channel_message(self):
        form = SendChannelMessageForm()
        if form.validate_on_submit():
            message = form.message.data
            murmur.send_message_all_channels('local', message)
            return redirect('/admin/tools/')
        return redirect('/admin/tools/')


## Login/Logout views
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


## Open ID after_login handler
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


## Error views
@app.errorhandler(404)
def page_not_found(error):
    return render_template('_error_pages/404.html'), 404


@app.errorhandler(500)
def page_not_found(error):
    return render_template('_error_pages/500.html'), 500


## Register flask-classy views
HomeView.register(app, route_base='/')
ServerView.register(app)
AdminView.register(app)
AdminServersView.register(app, route_prefix='/admin/', route_base='/servers')
AdminUsersView.register(app, route_prefix='/admin/', route_base='/users')
AdminHostsView.register(app, route_prefix='/admin/', route_base='/hosts')
AdminToolsView.register(app, route_prefix='/admin/', route_base='/tools')
