import uuid
import json
import datetime

from flask import render_template, request, redirect, url_for, jsonify
from flask.ext.classy import FlaskView, route
from flask.ext.mail import Message

import settings
from app.util import get_package_by_name
from app import db, tasks, mail
from app.forms import DeployTokenServerForm
from app.models import Server, Token
import app.murmur as murmur


class PaymentView(FlaskView):
    def index(self):
        return jsonify({
            "example": "example"
        })

    def post(self):
        print request.data["order"]
        return jsonify({
            "status": "received"
        })

    @route('/success', methods=['GET', 'POST'])
    def success(self):
        return render_template('payment/success.html')

    @route('/create/<id>', methods=['GET', 'POST'])
    def create(self, id):
        form = DeployTokenServerForm()
        token = Token.query.filter_by(uuid=id).first_or_404()
        package = get_package_by_name(token.package)

        ctx = {
            'slots': package.get('slots', None),
            'duration': package.get('duration', None)
        }

        if form.validate_on_submit():

            try:
                # Generate UUID
                gen_uuid = str(uuid.uuid4())

                # Create POST request to murmur-rest api to create a new server
                welcome_msg = "Welcome to Guildbit Mumble Hosting. View details on this server by " \
                              "<a href='http://guildbit.com/server/%s'>clicking here.</a>" % gen_uuid

                # Initialize payload for murmur-rest request
                payload = {
                    'password': form.password.data,
                    'welcometext': welcome_msg,
                    'users': ctx['slots'],
                    'registername': form.channel_name.data
                }

                # Create virtual murmur server and set SuperUser password
                server_id = murmur.create_server_by_location(form.location.data, payload)
                murmur.set_superuser_password(form.location.data, form.superuser_password.data, server_id)


                # Create database entry
                s = Server()
                s.duration = ctx['duration']
                s.password = form.password.data
                s.uuid = gen_uuid
                s.type = 'upgrade'
                s.mumble_instance = server_id
                s.mumble_host = murmur.get_murmur_hostname(form.location.data)

                # Expire token
                token.activation_date = datetime.datetime.utcnow()
                token.active = False
                db.session.add(s)
                db.session.add(token)
                db.session.commit()

                # Send task to delete server on expiration
                tasks.delete_server.apply_async([gen_uuid], eta=s.expiration)
                return redirect(url_for('ServerView:get', id=s.uuid))

            except:
                import traceback
                db.session.rollback()
                traceback.print_exc()

        return render_template('payment/create.html', form=form, token=token, ctx=ctx)

    @route('/callback', methods=['GET', 'POST'])
    def callback(self):
        """
        Coinbase callback receiver. Generates token and sends the code via email to user.
        @return:
        """

        ## Gather information from callback response

        data = json.loads(request.data)
        order = data.get("order", None)
        customer = data.get("customer", None)

        email = customer["email"]
        id = order["id"]
        status = order["status"]
        custom = order["custom"]
        button = order["button"]
        button_name = button["name"]

        ## Generate Token and store in database
        gen_uuid = str(uuid.uuid4())

        try:
            t = Token()
            t.uuid = gen_uuid
            t.email = email
            t.active = True
            t.package = custom

            db.session.add(t)
            db.session.commit()
        except:
            import traceback
            db.session.rollback()
            traceback.print_exc()

        ## Send email to user with unique link
        try:
            template = """
                        <p>Thank you for your order with Guildbit</p>
                        <p>You have ordered the package: <strong>%s</strong></p>
                        <p>Please use the following link to create your server:<br />
                        <a href='http://guildbit.com/payment/create/%s'>http://guildbit.com/payment/create/%s</a></p><br />
                        <p>If you have any questions, please feel free to <a href='http://guildbit.com/contact'>contact
                        us</a>.</p>""" % (button_name, gen_uuid, gen_uuid)

            msg = Message(
                "Guildbit - Order Confirmation",
                sender=settings.DEFAULT_MAIL_SENDER,
                recipients=[email])

            msg.html = template
            mail.send(msg)
        except:
            import traceback
            traceback.print_exc()

        return jsonify({
            "status": "received"
        })


    @route('/paypal-gateway', methods=['GET', 'POST'])
    def paypal_gateway(self):
        """
        Paypal callback receiver. Generates token and sends the code via email to user.
        @return:
        """

        print request.form
        first_name = request.form.get("first_name", None)
        last_name = request.form.get("last_name", None)
        payer_id = request.form.get("payer_id", None)
        payer_email = request.form.get("payer_email", None)
        item_name = request.form.get("item_name", None)
        item_number = request.form.get("item_number", None)
        custom = request.form.get("custom", None)
        payment_gross = request.form.get("payment_gross", None)

        ## Generate Token and store in database
        gen_uuid = str(uuid.uuid4())

        try:
            t = Token()
            t.uuid = gen_uuid
            t.email = payer_email
            t.active = True
            t.package = item_name

            db.session.add(t)
            db.session.commit()
        except:
            import traceback
            db.session.rollback()
            traceback.print_exc()

        ## Send email to user with unique link
        try:
            template = """
                        <p>Thank you for your order with Guildbit</p>
                        <p>You have ordered the package: <strong>%s</strong></p>
                        <p>Please use the following link to create your server:<br />
                        <a href='http://guildbit.com/payment/create/%s'>http://guildbit.com/payment/create/%s</a></p><br />
                        <p>If you have any questions, please feel free to <a href='http://guildbit.com/contact'>contact
                        us</a>.</p>""" % (item_name, gen_uuid, gen_uuid)

            msg = Message(
                "Guildbit - Order Confirmation",
                sender=settings.DEFAULT_MAIL_SENDER,
                recipients=[payer_email])

            msg.html = template
            mail.send(msg)
        except:
            import traceback
            traceback.print_exc()

        return jsonify({
            "status": "received"
        })
