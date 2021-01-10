import uuid

from flask import render_template, request, redirect, jsonify
from flask_classy import FlaskView, route
from flask_login import login_required
import psutil

import settings
from app.util import admin_required
from app import db
from app.forms import UserAdminForm, DeployCustomServerForm, NoticeForm, SuperuserPasswordForm
from app.forms import SendChannelMessageForm, CreateTokenForm, CleanupExpiredServersForm, build_hosts_list
from app.models import Server, User, Notice, Rating, Token
import app.murmur as murmur

ITEMS_PER_PAGE = 50


## Admin views
class AdminView(FlaskView):
    """
    All base admin views.
    """

    @login_required
    @admin_required
    def index(self):
        stats = murmur.get_all_server_stats()
        users_count = User.query.count()
        servers_count = Server.query.count()
        feedback_count = Rating.query.count()
        feedback_avg = Rating.get_rating_average()
        tokens_count = Token.query.count()

        ps = psutil

        ctx = {
            'servers_online': stats['servers_online'],
            'users_online': stats['users_online'],
            'users': users_count,
            'servers': servers_count,
            'feedback': feedback_count,
            'feedback_avg': feedback_avg,
            'tokens': tokens_count,
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
        page = int(request.args.get('page', 1))
        stats = murmur.get_all_server_stats()
        stats_ctx = {
            'servers_online': stats.get('servers_online'),
            'users_online': stats.get('users_online')
        }

        if filter == "all":
            servers = Server.query.order_by(Server.id.desc()).paginate(page, ITEMS_PER_PAGE, False)
        elif filter == "active":
            servers = Server.query.filter_by(status="active").order_by(Server.id.desc()).paginate(page, ITEMS_PER_PAGE, False)
        elif filter == "expired":
            servers = Server.query.filter_by(status="expired").order_by(Server.id.desc()).paginate(page, ITEMS_PER_PAGE, False)
        elif filter == "upgrade":
            servers = Server.query.filter_by(type="upgrade").order_by(Server.id.desc()).paginate(page, ITEMS_PER_PAGE, False)
        elif filter == "custom":
            servers = Server.query.filter_by(type="custom").order_by(Server.id.desc()).paginate(page, ITEMS_PER_PAGE, False)
        else:
            servers = Server.query.filter_by(status="active").order_by(Server.id.desc()).paginate(page, ITEMS_PER_PAGE, False)

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


class AdminPortsView(FlaskView):
    """
    Admin Ports view.
    """

    @login_required
    @admin_required
    def index(self):
        filter = request.args.get('filter')
        stats = murmur.get_all_server_stats()
        stats_ctx = {
            'servers_online': stats.get('servers_online'),
            'users_online': stats.get('users_online')
        }
        server_list = build_hosts_list()
        if filter is not None:
            ports = murmur.list_all_servers(filter)
        else:
            ports = murmur.list_all_servers(server_list[0][0])

        return render_template('admin/ports.html', ports=ports, stats=stats_ctx, server_list=server_list, title="Ports")


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
        superuser_pw_form = SuperuserPasswordForm()
        cleanup_form = CleanupExpiredServersForm()
        return render_template('admin/tools.html', notice_form=notice_form, message_form=message_form,
                               superuser_pw_form=superuser_pw_form, cleanup_form=cleanup_form, title="Tools")

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
            location = form.location.data
            message = form.message.data
            murmur.send_message_all_channels(location, message)
            return redirect('/admin/tools/')
        return redirect('/admin/tools/')

    @login_required
    @admin_required
    @route('/set-superuser-pw', methods=['POST'])
    def set_superuser_password(self):
        form = SuperuserPasswordForm()
        if form.validate_on_submit():
            location = form.location.data
            password = form.password.data
            instance = form.instance.data
            murmur.set_superuser_password(location, password, instance)
            return redirect('/admin/tools/')
        return redirect('/admin/tools/')

    @login_required
    @admin_required
    @route('/cleanup-expired-servers', methods=['POST'])
    def cleanup_expired_servers(self):
        form = CleanupExpiredServersForm()

        if form.validate_on_submit():
            location = form.location.data
            hostname = murmur.get_host_by_location(location)['hostname']

            servers = Server.query.filter_by(status='active', type='temp', mumble_host=hostname).all()
            expired = [s.mumble_instance for s in servers if s.is_expired]  # Filter servers if it should be expired.

            for s in servers:
                if s.is_expired:
                    s.status = 'expired'
                    db.session.add(s)

            try:
                db.session.commit()
                murmur.cleanup_expired_servers(location, expired)
                return redirect('/admin/tools/')
            except:
                db.session.rollback()
                raise

        return redirect('/admin/tools/')

    @login_required
    @admin_required
    @route('/list-instances', methods=['GET', 'POST'])
    def list_instances(self):
        instances = murmur.list_murmur_instances("atom")
        return jsonify(instances=instances)


class AdminFeedbackView(FlaskView):
    @login_required
    @admin_required
    def index(self):
        page = int(request.args.get('page', 1))
        feedback = Rating.query.order_by(Rating.id.desc()).paginate(page, ITEMS_PER_PAGE, False)
        return render_template('admin/feedback.html', feedback=feedback, title="Feedback")


class AdminTokensView(FlaskView):
    @login_required
    @admin_required
    def index(self):
        form = CreateTokenForm()
        tokens = Token.query.order_by(Token.id.desc()).all()
        return render_template('admin/tokens.html', form=form, tokens=tokens, title="Tokens")

    @login_required
    @admin_required
    def post(self):
        form = CreateTokenForm()
        tokens = Token.query.order_by(Token.id.desc()).all()
        if form.validate_on_submit():
            try:
                # Generate UUID
                gen_uuid = str(uuid.uuid4())

                # Create database entry
                t = Token()
                t.uuid = gen_uuid
                t.email = form.email.data or None
                t.active = True
                t.package = form.package.data

                db.session.add(t)
                db.session.commit()
                return redirect('/admin/tokens/')

            except:
                import traceback
                db.session.rollback()
                traceback.print_exc()
                return redirect('/admin/tokens/')


            return render_template('admin/tokens.html', form=form, tokens=tokens)
        return render_template('admin/tokens.html', form=form, tokens=tokens)
