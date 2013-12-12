## GuildBit Installation Guide

Installation instructions on deploying the frontend of GuildBit, as well as the murmur-rest backend,
server configuration, task queue and security. This is a complete guild for a production setup. This will all soon be
written into a Dockerfile for easy deployment and configuration.

#### Create VPS

Create an Ubuntu 13.10 box with your favorite VPS host. Digital Ocean 512MB is good enough.

#### Add New User and Secure Server

Instructions borrowed from https://library.linode.com/securing-your-server.

1. Login via SSH
2. `adduser example_user`
3. `usermod -a G sudo example_user`
4. Logout and log back in as example_user@host
5. Setup SSH Key Pair Auth for security
6. Symlink firewall rules with supplied iptables.firewall.rules file

`sudo ln -s /etc/iptables.firewall.rules`

7. Activate firewall rules

`sudo iptables-restore < /etc/iptables.firewall.rules`

8. Double check firewall rules

`sudo iptables -L`

9. Apply firewall rules on server startup

`sudo vim /etc/network/if-pre-up.d/firewall`

10. Add the following:

```bash
#!/bin/sh
/sbin/iptables-restore < /etc/iptables.firewall.rules
```

11. Set permissions

`sudo chmod +x /etc/network/if-pre-up.d/firewall`

12. Set up fail2ban

`sudo apt-get install fail2ban`

Server is secured.

#### Install and setup Nginx

1. Add stable repo and install nginx

```bash
sudo apt-add-repository ppa:nginx/stable
sudo apt-get update
sudo apt-get install nginx
```

2. Add supplied guildbit.com nginx config.

3. Restart Nginx

`sudo service nginx restart`

### Create and setup app

1. Create directories and chown them:

```
sudo mkdir /srv/guildbit
sudo mkdir /srv/murmur-rest
sudo chown alf:alf /srv/guildbit
sudo chown alf:alf /srv/murmur-rest
```

2. Install Python dependencies

```
sudo easy_install pip
sudo apt-get install python python-dev python-setuptools
sudo apt-get install python-software-properties
sudo pip install virtualenv
```

3. Setup guildbit app
upload project to directory

```
cd /srv/guildbit
virtualenv env --system-site-packages
. env/bin/activate
pip install -r requirements.txt
pip install gunicorn eventlet celery
```

4. Setup murmur-rest app

```
sudo apt-get install python-zeroc-ice
cd /srv/murmur-rest
virtualenv env --system-site-packages
. env/bin/activate
pip install -r requirements.txt
```

### Setup Mumble Server

Install Deps

```
sudo apt-get install mumble-server
sudo dpkg-reconfigure mumble-server
```

Use supplied mumble-server.ini file

`sudo ln -s `

### Install supervisor for running apps

Install supervisord

```
sudo pip install supervisord
sudo sh -c 'echo_supervisord_conf > /etc/supervisord.conf'
```

Use supplied supervisor.conf file

`ln -s`

Restart supervisord

```
sudo unlink /tmp/supervisor.sock
supervisord
```
