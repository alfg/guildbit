from flask import render_template, request, redirect, url_for, jsonify
from flask.ext.classy import FlaskView, route

from app import db
from app.models import Server, Rating
import app.murmur as murmur


## Stats views
class StatsView(FlaskView):
    def index(self):
        return "test"

    def json(self):
        return jsonify(test="test")
