import uuid
import json
import datetime

from flask import render_template, request, redirect, url_for, jsonify
from flask_classy import FlaskView, route
from flask_mail import Message

import settings
from app import db, tasks, mail
from app.forms import DeployTokenServerForm, get_active_hosts_by_type
from app.models import Server, Token, Package
from app import murmur


class PaymentView(FlaskView):
    @route('/success', methods=['GET', 'POST'])
    def success(self):
        return render_template('payment/success.html')

    @route('/create/<id>', methods=['GET', 'POST'])
    @route('/redeem/<id>', methods=['GET', 'POST'])
    def create(self, id):
        form = DeployTokenServerForm()
        form.region.choices = get_active_hosts_by_type('upgrade')
        token = Token.query.filter_by(uuid=id).first_or_404()
        package = Package.query.filter_by(id=token.package_id).first_or_404()

        ctx = {
            'slots': package.slots,
            'duration': package.duration
        }

        if form.validate_on_submit():
            try:
                # Generate UUID
                gen_uuid = str(uuid.uuid4())

                # Create POST request to murmur-rest api to create a new server
                welcome_msg = render_template("mumble/upgrade_welcome_message.html", gen_uuid=gen_uuid)

                # Initialize payload for murmur-rest request
                payload = {
                    'password': form.password.data,
                    'welcometext': welcome_msg,
                    'users': ctx['slots'],
                    'registername': form.channel_name.data
                }

                # Create virtual murmur server and set SuperUser password
                server_id = murmur.create_server_by_region(form.region.data, payload)
                murmur.set_superuser_password(form.region.data, form.superuser_password.data, server_id)

                # Create database entry
                s = Server()
                s.duration = ctx['duration']
                s.password = form.password.data
                s.uuid = gen_uuid
                s.type = 'upgrade'
                s.mumble_instance = server_id
                s.mumble_host = murmur.get_murmur_hostname(form.region.data)
                s.cvp_uuid = str(uuid.uuid4())
                s.status = 'active'

                # Expire token
                token.activation_date = datetime.datetime.utcnow()
                token.active = False
                token.email = form.email.data
                db.session.add(s)
                db.session.add(token)
                db.session.commit()

                # Send task to delete server on expiration
                tasks.delete_server.apply_async([gen_uuid], eta=s.expiration)

                # Send email to user if email was set
                if form.email.data is not None:
                    email_ctx = {
                        'url': 'http://guildbit.com/server/%s' % gen_uuid,
                        'package': token.package,
                        'expiration': 'expiration here',
                        'superuser_password': form.superuser_password.data
                    }
                    msg = Message(
                        "Guildbit - Server Created",
                        sender=settings.DEFAULT_MAIL_SENDER,
                        recipients=[form.email.data])

                    msg.html = render_template("emails/payment_server_created.html", ctx=email_ctx)
                    try:
                        mail.send(msg)
                    except:
                        import traceback
                        traceback.print_exc()

                return redirect(url_for('ServerView:get', uuid=s.uuid))

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

        # Gather information from callback response
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
            msg = Message(
                "Guildbit - Order Confirmation",
                sender=settings.DEFAULT_MAIL_SENDER,
                recipients=[email])

            # msg.html = template
            msg.html = render_template("emails/payment_thankyou.html", package=button_name, uuid=gen_uuid)
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

        print(request.form)

        # Gather information from callback response
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
            t.package_id = item_number

            db.session.add(t)
            db.session.commit()
        except:
            import traceback
            db.session.rollback()
            traceback.print_exc()

        ## Send email to user with unique link
        try:
            msg = Message(
                "Guildbit - Order Confirmation",
                sender=settings.DEFAULT_MAIL_SENDER,
                recipients=[payer_email])

            msg.html = render_template("emails/payment_thankyou.html", package=item_name, uuid=gen_uuid)
            mail.send(msg)
        except:
            import traceback
            traceback.print_exc()

        return jsonify({
            "status": "received"
        })
