"""
murmur.py
All murmur utility functions and logic for interfacing with configured murmur servers.
"""

import requests
from requests.auth import HTTPDigestAuth

from settings import MURMUR_HOSTS, DEFAULT_MURMUR_PORT

##
## Helper functions to load configs from settings
##


def get_host_by_location(location):
    """
    Searches MURMUR_HOSTS settings and returns tuple of address, uri, and hostname for given location.
    """
    for i in MURMUR_HOSTS:
        for k, v in i.iteritems():
            if v == location:
                return {
                    'address': i['address'],
                    'uri': i['uri'],
                    'hostname': i['hostname'],
                    'http_uri': i['http_uri'],
                    'username': i['username'],
                    'password': i['password']
                }
            else:
                pass
    return {}


def get_murmur_hostname(location):
    """
    Shortcut for getting murmur's hostname.
    """
    host = get_host_by_location(location)
    return host.get('hostname', None)


def get_http_uri(location):
    """
    Shortcut for getting murmur's hostname.
    """
    host = get_host_by_location(location)
    return host.get('http_uri', None)


def get_murmur_uri(location):
    """
    Shortcut for getting murmur's uri.
    @rtype : dict
    """
    host = get_host_by_location(location)
    return host.get('uri', None)


def get_murmur_credentials(location):
    """
    Shortcut for getting murmur's credentials for specified location.
    """

    host = get_host_by_location(location)
    username = host.get('username', None)
    password = host.get('password', None)
    return {'username': username, 'password': password}


def list_murmur_instances(location):
    """
    Lists all instances and ports for specified location.
    @param location:
    @return: list of instances and ports
    """
    servers = list_all_servers(location)
    instances = []

    for i in servers:
        instances.append(i['id'])

    return instances


##
## Functions to interface with murmur-rest server
##

def create_server(host, payload):
    """
    Accepts host and POST data payload as parameters and returns the id of the server created at host.
    """
    auth = get_murmur_credentials(host)
    r = requests.post(host + "/servers/", data=payload, auth=HTTPDigestAuth(auth['username'], auth['password']))
    server_id = r.json()['id']
    return server_id


def create_server_by_location(location, payload):
    """
    Accepts location and POST data payload as parameters and returns the id of the server created at host.
    """
    host = get_host_by_location(location)['uri']
    auth = get_murmur_credentials(location)
    port_check = find_available_port(location)

    # Set port if there's an open port
    if port_check is not None:
        payload["port"] = port_check

    try:
        r = requests.post(host + "/servers/", data=payload, auth=HTTPDigestAuth(auth['username'], auth['password']))
        if r.status_code == 200:
            server_id = r.json()['id']
            return server_id
    except requests.exceptions.ConnectionError as e:
        import traceback
        traceback.print_exc()
        return None
    return None


def get_server(host, instance_id):
    """
    Accepts host location (sf.guildbit.com), and mumble_instance id and returns dict of server information.
    """
    uri = get_murmur_uri(host)
    auth = get_murmur_credentials(host)

    if uri is not None:
        try:
            r = requests.get("%s/servers/%i" % (uri, instance_id), auth=HTTPDigestAuth(auth['username'],
                                                                                       auth['password']))
            if r.status_code == 200:
                return r.json()
        except requests.exceptions.ConnectionError as e:
            import traceback
            traceback.print_exc()
            return None
    else:
        return None


def delete_server(host, instance_id):
    """
    Deletes a server by hostname and instance_id.
    """
    uri = get_murmur_uri(host)
    auth = get_murmur_credentials(host)
    try:
        r = requests.delete("%s/servers/%i" % (uri, instance_id), auth=HTTPDigestAuth(auth['username'],
                                                                                      auth['password']))
        if r.status_code == 200:
            return r.json()
    except requests.exceptions.ConnectionError as e:
        import traceback
        traceback.print_exc()
        return None
    return None


def get_server_stats(host):
    """
    Get server stats for one host.
    """
    uri = get_murmur_uri(host)
    auth = get_murmur_credentials(host)
    try:
        r = requests.get("%s/stats/" % uri, auth=HTTPDigestAuth(auth['username'],
                                                                       auth['password']))
        if r.status_code == 200:
            stats = {
                'servers_online': r.json()['booted_servers'],
                'users_online': r.json()['users_online']
            }
            return stats
    except requests.exceptions.ConnectionError as e:
        import traceback
        traceback.print_exc()
        pass
    stats = {
        'servers_online': 0,
        'users_online': 0
    }
    return stats


def get_all_server_stats():
    """
    Get server stats for all hosts.
    """
    stats = {
        'servers_online': 0,
        'users_online': 0
    }
    for i in MURMUR_HOSTS:
        try:
            s = get_server_stats(i['hostname'])
            stats['servers_online'] += s.get('servers_online', 0)
            stats['users_online'] += s.get('users_online', 0)
        except:
            pass
    return stats


def get_server_logs(host, instance_id):
    """
    Get server logs for specified host and instance.
    """
    uri = get_murmur_uri(host)
    auth = get_murmur_credentials(host)
    if uri is not None:
        try:
            r = requests.get("%s/servers/%s/logs" % (uri, instance_id), auth=HTTPDigestAuth(auth['username'],
                                                                                                   auth['password']))
            if r.status_code == 200:
                logs = r.json()
                return logs
        except requests.exceptions.ConnectionError as e:
            import traceback
            traceback.print_exc()
            pass
    logs = []
    return logs


def send_message_all_channels(host, message):
    """
    Send a message to all channels on host.
    """
    uri = get_murmur_uri(host)
    auth = get_murmur_credentials(host)
    servers_list = requests.get('%s/servers/' % uri)
    server_ids_list = [i['id'] for i in servers_list.json()]

    for i in server_ids_list:
        try:
            r = requests.post("%s/servers/%s/sendmessage" % (uri, i),
                              data={'message': message},
                              auth=HTTPDigestAuth(auth['username'], auth['password']))
        except requests.exceptions.ConnectionError as e:
            import traceback
            traceback.print_exc()
    return


def list_all_servers(location):
    """
    Lists all servers for specified location
    @param location: location from config
    @return: list
    """
    uri = get_murmur_uri(location)
    auth = get_murmur_credentials(location)

    if uri is not None:
        try:
            r = requests.get("%s/servers/" % uri, auth=HTTPDigestAuth(auth['username'], auth['password']))
            if r.status_code == 200:
                return r.json()
        except requests.exceptions.ConnectionError as e:
            import traceback
            traceback.print_exc()
            return None
    else:
        return None


def set_superuser_password(location, password, instance_id):
    """
    Sets SuperUser password.
    @param location: server location from config
    @param password: password
    @param instance_id: instance id of virtual mumble server
    @return:
    """
    host = get_host_by_location(location)['uri']
    auth = get_murmur_credentials(location)
    payload = {'password': password}

    try:
        r = requests.post(host + "/servers/%i/setsuperuserpw" % instance_id, data=payload, auth=HTTPDigestAuth(auth['username'], auth['password']))
        if r.status_code == 200:
            return "SuperUser password set."
    except requests.exceptions.ConnectionError as e:
        import traceback
        traceback.print_exc()
        return None
    return None


def stop_server(host, instance_id):
    """
    Stops a server by host and id.
    @param host:
    @param instance_id:
    @return:
    """
    return

def start_server(host, instance_id):
    """
    Starts server by host and id.
    @param host:
    @param instance_id:
    @return:
    """
    return

##
## Utilities for interfacing with murmur servers
##

def find_available_port(location):
    """
    Scans all active ports in use and selects the next available port.
    @param location: location of mumble server instance from config
    @return: Port number
    """

    start_port = DEFAULT_MURMUR_PORT

    # Query list of active ports
    servers = list_all_servers(location)

    # Set active and inactive port lists. Initialize the start port.
    active_ports = [start_port]

    # Add all active ports to the active list
    for i in servers:
        active_ports.append(i["port"])

    # Find inactive ports and build a set
    lowest_item = min(active_ports)
    highest_item = max(active_ports)
    full_set = set(xrange(lowest_item, highest_item + 1))
    inactive_ports = full_set - set(active_ports)

    # Sort lists
    active_ports = sorted(active_ports)
    inactive_ports = sorted(inactive_ports)

    print "Active ports:", active_ports
    print "Inactive ports: ", inactive_ports

    # If any inactive ports, then use the first item. Otherwise, use the last active port + 1
    if inactive_ports:
        chosen_port = inactive_ports[0]
    else:
        chosen_port = active_ports[-1] + 1

    print "Next available port: %s" % chosen_port
    return chosen_port
