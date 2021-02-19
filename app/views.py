import re

from flask import render_template, request, redirect, session, url_for, g, flash, json
from flask_login import login_user, logout_user, current_user

import settings
from app import app, db, lm, oid, cache, babel

from app.controllers.home import HomeView
from app.controllers.server import ServerView
from app.controllers.admin import AdminView, AdminServersView, AdminPortsView, AdminHostsView, AdminFeedbackView
from app.controllers.admin import AdminTokensView, AdminToolsView, AdminUsersView, AdminPackagesView, AdminBansView
from app.controllers.payment import PaymentView

from app.forms import LoginForm
from app.models import User, Notice, ROLE_USER
from app.util import get_steam_userinfo


## Flask-babel localization
@babel.localeselector
def get_locale():
    language = request.cookies.get('language')
    if language:
        return language
    return request.accept_languages.best_match(settings.LANGUAGES.keys())


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


@oid.after_login
def after_login(resp):
    _steam_id_re = re.compile('steamcommunity.com/openid/id/(.*?)$')

    match = _steam_id_re.search(resp.identity_url)
    g.user = User.get_or_create(match.group(1))
    steam_data = get_steam_userinfo(g.user.steam_id)
    g.user.nickname = steam_data['personaname']
    db.session.commit()
    session['user_id'] = g.user.id
    flash('You are logged in as %s' % g.user.nickname)
    return redirect(oid.get_next_url())


## Error views
@app.errorhandler(404)
def page_not_found(error):
    return render_template('error_pages/404.html'), 404


@app.errorhandler(500)
def page_not_found(error):
    return render_template('error_pages/500.html'), 500


## Register flask-classy views
HomeView.register(app, route_base='/')
ServerView.register(app)
PaymentView.register(app)
AdminView.register(app)
AdminServersView.register(app, route_prefix='/admin/', route_base='/servers')
AdminPortsView.register(app, route_prefix='/admin/', route_base='/ports')
AdminUsersView.register(app, route_prefix='/admin/', route_base='/users')
AdminHostsView.register(app, route_prefix='/admin/', route_base='/hosts')
AdminToolsView.register(app, route_prefix='/admin/', route_base='/tools')
AdminFeedbackView.register(app, route_prefix='/admin/', route_base='/feedback')
AdminTokensView.register(app, route_prefix='/admin/', route_base='/tokens')
AdminPackagesView.register(app, route_prefix='/admin/', route_base='/packages')
AdminBansView.register(app, route_prefix='/admin/', route_base='/bans')
