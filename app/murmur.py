"""
murmur.py
All murmur utility functions and logic for interfacing with configured murmur servers.
"""

import requests
from requests.auth import HTTPDigestAuth

from settings import DEFAULT_MURMUR_PORT
from app.models import Host

##
## Helper functions to load configs from settings
##


def get_host_by_region(region):
    """
    Searches Hosts and returns tuple of uri for given region.
    """
    hosts = Host.get_all_hosts()
    for host in hosts:
        if host.region == region:
            return {
                'name': host.name,
                'region': host.region,
                'uri': host.uri,
                'active': host.active,
                'type': host.type,
                'hostname': host.hostname,
                'username': host.username,
                'password': host.password 
            }
        else:
            pass
    return {}

def get_host_by_hostname(hostname):
    """
    Searches Hosts and returns tuple of uri for given region.
    """
    hosts = Host.get_all_hosts()
    for host in hosts:
        if host.hostname == hostname:
            return {
                'name': host.name,
                'region': host.region,
                'uri': host.uri,
                'active': host.active,
                'type': host.type,
                'hostname': host.hostname,
                'username': host.username,
                'password': host.password 
            }
        else:
            pass
    return {}


def get_murmur_hostname(region):
    """
    Shortcut for getting murmur's hostname.
    """
    host = get_host_by_region(region)
    return host.get('hostname', None)

def get_murmur_uri(region):
    """
    Shortcut for getting murmur's uri.
    @rtype : dict
    """
    host = get_host_by_region(region)
    return host.get('uri', None)

def get_murmur_credentials(region):
    """
    Shortcut for getting murmur's credentials for specified region.
    """

    host = get_host_by_region(region)
    username = host.get('username', None)
    password = host.get('password', None)
    return {'username': username, 'password': password}


def list_murmur_instances(region):
    """
    Lists all instances and ports for specified region.
    @param region:
    @return: list of instances and ports
    """
    servers = list_all_servers(region)
    instances = []

    for i in servers:
        instances.append(i['id'])

    return instances


##
## Functions to interface with murmur-rest server
##

def create_server(hostname, payload):
    """
    Accepts host and POST data payload as parameters and returns the id of the server created at host.
    """
    host = get_host_by_hostname(hostname)
    auth = get_murmur_credentials(host['region'])
    r = requests.post(host + "/servers/", data=payload, auth=HTTPDigestAuth(auth['username'], auth['password']))
    server_id = r.json()['id']
    return server_id


def create_server_by_region(region, payload):
    """
    Accepts region and POST data payload as parameters and returns the id of the server created at host.
    """
    host = get_host_by_region(region)
    port_check = find_available_port(host['region'])

    # Set port if there's an open port
    if port_check is not None:
        payload["port"] = port_check

    try:
        r = requests.post(host['uri'] + "/servers/", data=payload, auth=HTTPDigestAuth(host['username'], host['password']))
        if r.ok:
            server_id = r.json()['id']
            return server_id
    except requests.exceptions.ConnectionError as e:
        import traceback
        traceback.print_exc()
        return None
    return None


def get_server(hostname, instance_id):
    """
    Accepts host region (sf.guildbit.com), and mumble_instance id and returns dict of server information.
    """
    host = get_host_by_hostname(hostname)

    if host['uri'] is not None:
        try:
            r = requests.get("%s/servers/%i" % (host['uri'], instance_id),
                                                auth=HTTPDigestAuth(host['username'],
                                                                    host['password']))
            if r.ok:
                return r.json()
        except requests.exceptions.ConnectionError as e:
            import traceback
            traceback.print_exc()
            return None
    else:
        return None


def delete_server(hostname, instance_id):
    """
    Deletes a server by hostname and instance_id.
    """
    host = get_host_by_hostname(hostname)

    try:
        r = requests.delete("%s/servers/%i" % (host['uri'], instance_id), auth=HTTPDigestAuth(host['username'],
                                                                                      host['password']))
        if r.ok:
            return r.json()
    except requests.exceptions.ConnectionError as e:
        import traceback
        traceback.print_exc()
        return None
    return None


def get_server_stats(region):
    """
    Get server stats for one host.
    """
    host = get_host_by_region(region)

    try:
        r = requests.get("%s/stats/" % host['uri'], auth=HTTPDigestAuth(host['username'],
                                                                        host['password']))
        if r.ok:
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
    hosts = Host.get_all_hosts()
    stats = {
        'servers_online': 0,
        'users_online': 0
    }
    for host in hosts:
        try:
            s = get_server_stats(host.region)
            stats['servers_online'] += s.get('servers_online', 0)
            stats['users_online'] += s.get('users_online', 0)
        except:
            pass
    return stats


def get_server_logs(hostname, instance_id):
    """
    Get server logs for specified host and instance.
    """
    host = get_host_by_hostname(hostname)

    if host['uri'] is not None:
        try:
            r = requests.get("%s/servers/%s/logs" % (host['uri'], instance_id),
                            auth=HTTPDigestAuth(host['username'],
                                                host['password']))
            if r.ok:
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
    host = get_host_by_hostname(hostname)
    servers_list = requests.get('%s/servers/' % host['uri'])
    server_ids_list = [i['id'] for i in servers_list.json()]

    for i in server_ids_list:
        try:
            r = requests.post("%s/servers/%s/sendmessage" % (host['uri'], i),
                              data={'message': message},
                              auth=HTTPDigestAuth(host['username'], host['password']))
        except requests.exceptions.ConnectionError as e:
            import traceback
            traceback.print_exc()
    return


def list_all_servers(region):
    """
    Lists all servers for specified region
    @param region: region from config
    @return: list
    """
    uri = get_murmur_uri(region)
    auth = get_murmur_credentials(region)

    if uri is not None:
        try:
            r = requests.get("%s/servers/" % uri, auth=HTTPDigestAuth(auth['username'], auth['password']))
            if r.ok:
                return r.json()
        except requests.exceptions.ConnectionError as e:
            import traceback
            traceback.print_exc()
            return None
    else:
        return None


def set_superuser_password(region, password, instance_id):
    """
    Sets SuperUser password.
    @param region: server region from config
    @param password: password
    @param instance_id: instance id of virtual mumble server
    @return:
    """
    host = get_host_by_region(region)['uri']
    auth = get_murmur_credentials(region)
    payload = {'password': password}

    try:
        r = requests.post(host + "/servers/%i/setsuperuserpw" % instance_id, data=payload, auth=HTTPDigestAuth(auth['username'], auth['password']))
        if r.ok:
            return "SuperUser password set."
    except requests.exceptions.ConnectionError as e:
        import traceback
        traceback.print_exc()
        return None
    return None


def cleanup_expired_servers(region, expired_ids):
    """
    Cleans up expired servers.
    @param region: region from config
    @param expired_ids: list of mumble_instance IDs to be expired.
    @return: None
    """
    host = get_host_by_region(region)['uri']
    auth = get_murmur_credentials(region)
    expired_ids = ','.join(str(x) for x in expired_ids)

    try:
        r = requests.delete("%s/servers/delete?id=%s" % (host, expired_ids), auth=HTTPDigestAuth(auth['username'],
                                                                                      auth['password']))
        if r.ok:
            return r.json()
    except requests.exceptions.ConnectionError as e:
        import traceback
        traceback.print_exc()
        return None
    return None

##
## Utilities for interfacing with murmur servers
##


def find_available_port(hostname):
    """
    Scans all active ports in use and selects the next available port.
    @param region: region of mumble server instance from config
    @return: Port number
    """

    start_port = DEFAULT_MURMUR_PORT

    # Query list of active ports
    servers = list_all_servers(hostname)

    # Set active and inactive port lists. Initialize the start port.
    active_ports = [start_port]

    # Add all active ports to the active list
    for i in servers:
        active_ports.append(i["port"])

    # Find inactive ports and build a set
    lowest_item = min(active_ports)
    highest_item = max(active_ports)
    full_set = set(range(lowest_item, highest_item + 1))
    inactive_ports = full_set - set(active_ports)

    # Sort lists
    active_ports = sorted(active_ports)
    inactive_ports = sorted(inactive_ports)

    # print("Active ports:", active_ports)
    # print("Inactive ports: ", inactive_ports)

    # If any inactive ports, then use the first item. Otherwise, use the last active port + 1
    if inactive_ports:
        chosen_port = inactive_ports[0]
    else:
        chosen_port = active_ports[-1] + 1

    # print("Next available port: %s" % chosen_port)
    return chosen_port
