from functools import wraps

from flask.ext.login import current_user
from flask import redirect
import requests
from requests import ConnectionError

from settings import MURMUR_HOSTS, PACKAGES


def admin_required(fn):
    """
    View decorator to require an admin. ADMIN is ROLE = 1
    """
    @wraps(fn)
    def decorated_view(*args, **kwargs):
        if current_user.get_role() != 1:
            return redirect("/")
        return fn(*args, **kwargs)
    return decorated_view


def get_or_create(session, model, **kwargs):
    """ INACTIVE
    A get or create helper for SQLAlchemy
    """
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        return instance


def host_balancer():
    """ INACTIVE
    Checks the amount of murmur hosts in settings and returns a server depending on server instances load. Used for
    deciding which murmur host to use when deploying a new mumble instance.
    """

    hosts = MURMUR_HOSTS  # List of hosts defined in settings

    # Query stats for each murmur host in settings. Adds the booted_servers count as a key to the dict.
    servers_list = []
    for host in hosts:
        try:
            r = requests.get("%s/stats/" % host['uri'])

            if r.status_code == 200:
                host['booted_servers'] = r.json()['booted_servers']
                servers_list.append(host)

        except ConnectionError:
            # Don't add to servers_list if exception
            pass

    # Find the lowest populated server from the compiled servers_list and return the selected dict object
    if servers_list:
        lowest = min(servers_list, key=lambda x:x['booted_servers'])
    else:
        lowest = None

    return lowest


def get_package_by_name(name):
    """
    Searches MURMUR_HOSTS settings and returns tuple of address, uri, and hostname for given location.
    """
    for i in PACKAGES:
        for k, v in i.iteritems():
            if v == name:
                return {
                    'name': i['name'],
                    'slots': i['slots'],
                    'duration': i['duration']
                }
            else:
                pass
    return {}


