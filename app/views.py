from flask import render_template, request, redirect, session, url_for, g, flash
from flask.ext.login import login_user, logout_user, current_user

import settings
from app import app, db, lm, oid, cache, babel
from app.controllers.home import HomeView
from app.controllers.server import ServerView
from app.controllers.admin import AdminView, AdminServersView, AdminPortsView, AdminHostsView, AdminFeedbackView
from app.controllers.admin import AdminTokensView, AdminToolsView, AdminUsersView
from app.controllers.payment import PaymentView
from app.forms import LoginForm
from app.models import User, Notice, ROLE_USER


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
