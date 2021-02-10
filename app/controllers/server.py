from datetime import datetime, timedelta
import json

from flask import render_template, request, redirect, url_for, jsonify, Response, flash
from flask_classy import FlaskView, route

from app import db, cache
from app.models import Server, Rating
from app import murmur
from app.util import support_jsonp

from settings import SERVER_EXTENSIONS_MAX


## Server views
class ServerView(FlaskView):
    def index(self):
        return redirect(url_for('home'))

    def get(self, uuid):
        x_forwarded_for = request.headers.getlist('X-Forwarded-For');
        ip = x_forwarded_for[0] if x_forwarded_for else request.remote_addr

        server = Server.query.filter_by(uuid=uuid).first_or_404()
        if server.status == 'queued':
            return render_template('server_queued.html')

        rating = Rating.query.filter_by(server_uuid=uuid, ip=ip).first()
        host = murmur.get_host_by_hostname(server.mumble_host)

        server_details = murmur.get_server(server.mumble_host, server.mumble_instance)
        if not server_details:
            return render_template('server_expired.html', server=server, rating=rating)

        return render_template('server.html', server=server, details=server_details, host=host, rating=rating, ip=ip, extensions_max=SERVER_EXTENSIONS_MAX)

    @route('/<uuid>/expired')
    def expired(self, uuid):
        x_forwarded_for = request.headers.getlist('X-Forwarded-For');
        ip = x_forwarded_for[0] if x_forwarded_for else request.remote_addr

        server = Server.query.filter_by(uuid=uuid).first_or_404()
        rating = Rating.query.filter_by(server_uuid=uuid, ip=ip).first()
        return render_template('server_expired.html', server=server, rating=rating)

    @cache.cached(timeout=30)
    @route('/<uuid>/users/')
    def users(self, uuid):
        server = Server.query.filter_by(uuid=uuid).first_or_404()
        server_details = murmur.get_server(server.mumble_host, server.mumble_instance)
        if server_details is not None:
            users = {
                'count': server_details['user_count'],
                'users': server_details['users'],
                'sub_channels': server_details['sub_channels']
            }
            return jsonify(users=users)
        else:
            return jsonify(users=None)

    @route('/<id>/rating', methods=['POST'])
    @route('/<id>/expired/rating', methods=['POST'])
    def rating(self, id):
        x_forwarded_for = request.headers.getlist('X-Forwarded-For');
        ip = x_forwarded_for[0] if x_forwarded_for else request.remote_addr

        stars = request.form['stars']

        r = Rating.query.filter_by(server_uuid=id, ip=ip).first()

        if r is None:
            try:
                r = Rating()
                r.server_uuid = id
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
    @route('/<id>/expired/feedback', methods=['POST'])
    def feedback(self, id):
        x_forwarded_for = request.headers.getlist('X-Forwarded-For');
        ip = x_forwarded_for[0] if x_forwarded_for else request.remote_addr

        feedback = request.form['feedback']

        if feedback:
            try:
                r = Rating.query.filter_by(server_uuid=id, ip=ip).first()
                r.feedback = feedback
                db.session.commit()
            except:
                import traceback

                db.session.rollback()
                traceback.print_exc()

            return jsonify(message='success')

        return jsonify(message='error')

    @support_jsonp
    @cache.cached(timeout=10)
    @route('/cvp/<id>/')
    @route('/cvp/<id>/json/')
    def cvp(self, id):
        """
        CVP endpoint provides the Channel Viewer Protocol Specification according to Mumble documentation to allow
        embeddable widgets display live users on their websites.
        https://wiki.mumble.info/Channel_Viewer_Protocol
        @param id: server id
        @return: json response for cvp
        """

        server = Server.query.filter_by(cvp_uuid=id).first_or_404()
        server_details = murmur.get_server(server.mumble_host, server.mumble_instance)

        if server_details is not None:
            root_channel = server_details['parent_channel']
            sub_channels = server_details['sub_channels']

            # Iterate through channels to transform json response to cvp specification
            for i in sub_channels:
                i['description'] = i['c']['description']
                i['id'] = i['c']['id']
                i['links'] = i['c']['links']
                i['name'] = i['c']['name']
                i['parent'] = i['c']['parent']
                i['position'] = i['c']['position']
                i['temporary'] = i['c']['temporary']
                i['channels'] = i.pop('children')
                i['x_connecturl'] = "mumble://%s:%i" % (server.mumble_host, server_details['port'])

                i.pop("c", None)
                # Iterate through channels' sub-channels to transform json response to cvp specification
                for j in i['channels']:
                    j['description'] = j['c']['description']
                    j['id'] = j['c']['id']
                    j['links'] = j['c']['links']
                    j['name'] = j['c']['name']
                    j['parent'] = j['c']['parent']
                    j['position'] = j['c']['position']
                    j['temporary'] = j['c']['temporary']
                    j['x_connecturl'] = "mumble://%s:%i" % (server.mumble_host, server_details['port'])
                    j.pop("c", None)
                    j['channels'] = j.pop('children')

            # More reforming of json data to CVP spec.
            root_channel['channels'] = sub_channels
            root_channel['users'] = server_details['users']

            # Prepare json response context
            cvp = {
                'root': root_channel,
                'id': server_details['id'],
                'name': server_details['name'],
                "x_connecturl": "mumble://%s:%i" % (server.mumble_host, server_details['port']),
                'x_uptime': server_details['uptime']
            }
            return Response(json.dumps(cvp, sort_keys=True, indent=4), mimetype='application/json')

        else:
            return jsonify({'code': 404, 'message': 'Not Found'})

    ###
    # Controls
    ###

    @route('/<uuid>/delete', methods=['POST'])
    def delete_server(self, uuid):
        """
        UserControl: Deletes the server.
        @param id:
        @return:
        """
        x_forwarded_for = request.headers.getlist('X-Forwarded-For');
        ip = x_forwarded_for[0] if x_forwarded_for else request.remote_addr

        server = Server.query.filter_by(uuid=uuid, ip=ip).first_or_404()

        if server:
            try:
                murmur.delete_server(server.mumble_host, server.mumble_instance)
                server.status = "expired"
                db.session.commit()
                return redirect(url_for('ServerView:get', uuid=uuid))
            except:
                import traceback

                db.session.rollback()
                traceback.print_exc()
        return redirect(url_for('ServerView:get', uuid=uuid))

    @route('/<uuid>/extend', methods=['POST', 'GET'])
    def extend_server(self, uuid):
        """
        UserControl: Extends the server by 1 hour.
        @param id:
        @return:
        """

        limit = SERVER_EXTENSIONS_MAX  # Allowed extensions count

        x_forwarded_for = request.headers.getlist('X-Forwarded-For');
        ip = x_forwarded_for[0] if x_forwarded_for else request.remote_addr

        server = Server.query.filter_by(uuid=uuid, ip=ip).first_or_404()

        if server and server.extensions < limit:
            try:
                server.duration += 1
                server.extensions += 1
                db.session.commit()

                flash("Server extended for 1 hour.")
                return redirect(url_for('ServerView:get', uuid=uuid))

            except:
                import traceback
                db.session.rollback()
                traceback.print_exc()

        flash("Server already extended.")
        return redirect(url_for('ServerView:get', uuid=uuid))

