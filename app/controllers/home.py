import uuid

from flask import render_template, redirect, url_for, g, flash, request, make_response
from flask_classy import FlaskView, route
from flask_mail import Message

import settings
from app import db, cache, tasks, mail
from app.forms import DeployServerForm, ContactForm
from app.forms import duration_choices, get_active_hosts_by_type
from app.models import Server, Package, Ban
from app import murmur


## Home views
class HomeView(FlaskView):
    @route('/', endpoint='home')
    def index(self):
        user = g.user
        form = DeployServerForm()
        form.duration.choices = duration_choices()
        form.region.choices = get_active_hosts_by_type('free')
        return render_template('index.html', form=form)

    def post(self):
        # Set admin's IP.
        x_forwarded_for = request.headers.getlist('X-Forwarded-For');
        ip = x_forwarded_for[0] if x_forwarded_for else request.remote_addr
        ip = ip.split(',')[0]

        # Flash message if user is on banlist.
        banned = Ban.query.filter_by(ip=ip).first()
        if banned:
            flash("User banned! Reason: %s" % banned.reason)
            return redirect('/')



        form = DeployServerForm()
        form.duration.choices = duration_choices()
        form.region.choices = get_active_hosts_by_type('free')

        if form.validate_on_submit():
            try:
                # Generate UUID
                gen_uuid = str(uuid.uuid4())

                # Create database entry
                s = Server()
                s.duration = form.duration.data
                s.password = form.password.data
                s.uuid = gen_uuid
                s.mumble_instance = None
                s.mumble_host = None
                s.status = "queued"
                s.mumble_host = murmur.get_murmur_hostname(form.region.data)
                s.ip = ip
                db.session.add(s)
                db.session.commit()

                # Setup the payload and send to create_server queue.
                welcome_msg = render_template("mumble/temp_welcome_message.html", gen_uuid=gen_uuid)

                payload = {
                    'password': form.password.data,
                    'welcometext': welcome_msg,
                    'users': settings.DEFAULT_MAX_USERS,
                    'registername': settings.DEFAULT_CHANNEL_NAME
                }

                # Send task to create server
                tasks.create_server.apply_async([gen_uuid, form.region.data, payload])

                # Store server_uuid cookie and redirect.
                response = make_response(redirect(url_for('ServerView:get', uuid=s.uuid)))
                response.set_cookie('server_uuid', s.uuid)
                return response

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

    @cache.cached(timeout=10)
    @route('/upgrade/')
    def upgrade(self):
        packages = Package.query.filter_by(active=True).order_by(Package.order.asc()).all()
        regions = get_active_hosts_by_type('upgrade')
        return render_template('upgrade.html', regions=regions, packages=packages)

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
                    sender=form.email.data,
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

    @route('/redeem/<id>/', methods=['GET'])
    def redeem(self, id):
        return redirect('/payment/redeem/%s' % id)