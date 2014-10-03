import json

from flask import render_template, request, redirect, url_for, jsonify, Response
from flask.ext.classy import FlaskView, route

from app import db, cache
from app.models import Server, Rating
import app.murmur as murmur
from app.util import support_jsonp


## Server views
class ServerView(FlaskView):
    def index(self):
        return redirect(url_for('home'))

    def get(self, id):
        ip = request.remote_addr
        server = Server.query.filter_by(uuid=id).first_or_404()
        rating = Rating.query.filter_by(server_uuid=id, ip=ip).first()

        server_details = murmur.get_server(server.mumble_host, server.mumble_instance)
        if server_details is not None:
            return render_template('server.html', server=server, details=server_details, rating=rating, ip=ip)
        else:
            return render_template('server_expired.html', server=server, rating=rating)

    @route('/<id>/expired')
    def expired(self, id):
        ip = request.remote_addr
        server = Server.query.filter_by(uuid=id).first_or_404()
        rating = Rating.query.filter_by(server_uuid=id, ip=ip).first()
        return render_template('server_expired.html', server=server, rating=rating)

    @route('/<id>/users/')
    def users(self, id):
        server = Server.query.filter_by(uuid=id).first_or_404()
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
        ip = request.remote_addr
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
        ip = request.remote_addr
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
        http://mumble.sourceforge.net/Channel_Viewer_Protocol
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

    @route('/<id>/delete', methods=['POST'])
    def delete_server(self, id):
        """
        UserControl: Deletes the server.
        @param id:
        @return:
        """
        ip = request.remote_addr
        server = Server.query.filter_by(uuid=id, ip=ip).first_or_404()
        print server

        if server:
            try:
                murmur.delete_server(server.mumble_host, server.mumble_instance)
                server.status = "expired"
                db.session.commit()
                return redirect(url_for('ServerView:get', id=id))
            except:
                import traceback

                db.session.rollback()
                traceback.print_exc()
        return redirect(url_for('ServerView:get', id=id))

