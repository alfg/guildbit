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

        example = {
            "order": {
                "id": None,
                "created_at": None,
                "status": "completed",
                "event": None,
                "total_btc": {
                    "cents": 100000000,
                    "currency_iso": "BTC"
                },
                "total_native": {
                    "cents": 65273,
                    "currency_iso": "USD"
                },
                "total_payout": {
                    "cents": 65273,
                    "currency_iso": "USD"
                },
                "custom": "123456789",
                "receive_address": "1DwUndActWKnjfSYX2DP5GU3PtJAFaqAYJ",
                "button": {
                    "type": "buy_now",
                    "name": "Test Item",
                    "description": None,
                    "id": None
                },
                "transaction": {
                    "id": "53928c785fdf9bb7e6000024",
                    "hash": "4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b",
                    "confirmations": 0
                }
            }
        }

        # import json
        # test = json.loads(example)

        # example = example.get("order", None)
        #
        # order_id = example.get("id", None)
        # order_created_date = example.get("created_at", None)
        # order_status = example.get("status", None)
        #
        # print order_id
        # print order_created_date
        # print order_status

        return jsonify({
            "example": example
        })

    def post(self):
        print request.data["order"]
        return jsonify({
            "status": "received"
        })

    @route('/success')
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
                payload = {
                    'password': form.password.data,
                    'welcometext': welcome_msg,
                    'users': ctx['slots'],
                    'registername': form.channel_name.data
                }

                server_id = murmur.create_server_by_location(form.location.data, payload)

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
        Callback receiver. Generates token and sends the code via email to user.
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
                        <p>If you have any questions, please feel free to respond to this email.</p>
                       """ % (button_name, gen_uuid, gen_uuid)

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
