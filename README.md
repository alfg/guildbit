# GuildBit.com

This project is the frontend application of GuildBit.com. This project is built with the following stack:

* Flask as the Python Framework
* SQLAlchemy as the ORM for postgres/sqlite
* Celery messaging queue for scheduling Mumble Server tasks
* Redis as the message broker for Celery
* Requests for sending REST requests to murmur-rest
* Murmur-rest as the RESTful backend for communicating with Murmur virtual servers via Ice
* CSS Framework is Gumby


## Process

When a user deploys a GuildBit server from the frontpage, the following takes place:

1. Form is validated and a POST request is sent to the home controller index view
2. App server generates a UUID4
3. Form data is captured as the duration, password
4. A post request (via python requests) is sent to murmur-rest to create a server using the payload
5. murmur-rest returns an assigned server id
6. Database entry a saved with the following: uuid, form.duration, form.password, server.id
7. A scheduled date is generated based on the created_date from the database entry + form.duration hours
8. A celery task is scheduled using the info above
9. Server view is returned to user /server/{uuid4}

The server view checks database if server is expired. If expired, the server_expired.html view is shown.

## Install

For a full production deployment, please refer to [INSTALL.md](INSTALL.md).

To develop locally:

```bash
git clone https://github.com/alfg/guildbit
virtualenv env --system-site-packages
. env/bin/activate
pip install -r requirements
python runserver.py
```

You'll need to setup mumble-server, python-zeroc-ice, and murmur-rest to develop and test locally, or
configure `MURMUR_REST_HOST` to another server that's already setup.

Install instructions on [http://github.com/alfg/murmur-rest](http://github.com/alfg/murmur-rest)

Run celery to test and track queues:

`celery worker --app=app.tasks -l info`
