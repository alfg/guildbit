# GuildBit.com
> Free Mumble Hosting

![Guildbit.com](app/static/img/guildbit_logo2.png)

GuildBit is a full-stack application written in Python to offer
temporary virtual Mumble servers to users. Guildbit depends on [murmur-rest](https://github.com/alfg/murmur-rest) API backend to interface
with the virtual Mumble servers.

https://guildbit.com

## Screenshots

![Guildbit.com Home](screenshots/01_screenshot_home.png)
![Guildbit.com Server](screenshots/02_screenshot_server.png)
![Guildbit.com Admin](screenshots/03_screenshot_admin.png)

## Technology Stack
* [Flask](http://flask.pocoo.org/) - Python Framework
* [Flask-SQLAlchemy](http://flask-sqlalchemy.pocoo.org/) - PostgreSQL/SQLite ORM
* [Celery](http://www.celeryproject.org/) - Message Queue for scheduling Mumble Server tasks
* [Redis](http://redis.io/) - Cache backend and message broker for Celery
* [Python-requests](http://docs.python-requests.org/en/master/) - HTTP requests to murmur-rest API
* [Murmur-rest](https://github.com/alfg/murmur-rest) - Murmur HTTP API

## Development
It is highly recommended to use [Docker](https://www.docker.com/) to setup your environment. A `docker-compose.yml` is provided as a typical setup for the following services:
* Guildbit App
* Celery - Task scheduler.
* Flower - Celery Dashboard UI
* NGINX - optional reverse proxy
* Redis Server - key/value storage for caching and message broker
* murmur-rest - Murmur HTTP API 
* murmurd - Mumble Server

If using Docker, scroll down to [Docker Setup](#Docker)

### Requirements
* Redis-server
* PostgreSQL
* [Virtualenv](https://virtualenv.pypa.io/en/stable/) recommended for development
* [murmur-rest](https://github.com/alfg/murmur-rest)

*Please note `murmur-rest` MUST be setup in order to deploy virtual Mumble servers. However, it is possible to work on the Guildbit app without murmur-rest, you just won't be able to deploy or administer any Mumble servers.*


```bash
$ git clone https://github.com/alfg/guildbit
$ virtualenv env --system-site-packages
$ . env/bin/activate
$ pip install -r requirements.txt
$ export FLASK_ENV=development
$ export FLASK_RUN_HOST=0.0.0.0
$ export FLASK_RUN_PORT=5000
$ flask run

* Running on http://0.0.0.0:5000/
* Restarting with reloader
```
* Database and schema will automatically be created via Flask-Migrate.
* Development server is running with default settings. See [Configuration Guide](https://github.com/alfg/guildbit/wiki/Configuration-Guide) for additional configuration options.
* Run celery in a separate process (but in the same python environment) to start the messaging queue:
  ```
  $ celery worker --app=app.tasks -l info
  ```

### Docker
A Dockerfile and `docker-compose.yml` is provided for setting up a local development server. This will startup and link all services needed to run Guildbit:
```
$ docker-compose build
$ docker-compose up

Starting guildbit_redis_1   ... done
Starting guildbit_murmurd_1 ... done
Starting guildbit_db_1      ... done
Starting guildbit_flower_1  ... done
Starting guildbit_murmur-rest_1 ... done
Starting guildbit_guildbit_1    ... done
Starting guildbit_celery_1      ... done
Starting guildbit_nginx_1       ... done

guildbit_1 | [1] [INFO] Starting gunicorn 19.5.0
guildbit_1 | [1] [INFO] Listening at: http://0.0.0.0:8081 (1)
guildbit_1 | [1] [INFO] Using worker: sync
guildbit_1 | [9] [INFO] Booting worker with pid: 9
```

Or run `flask run` via Docker for active devleopment with a local volume mounted:
```
λ docker-compose run --service-ports guildbit bash
Starting guildbit_db_1      ... done
Starting guildbit_redis_1   ... done
Starting guildbit_murmurd_1 ... done
Starting guildbit_murmur-rest_1 ... done
Creating guildbit_guildbit_run  ... done
root@dbf0add00eec:/opt/guildbit# . venv/bin/activate
(venv) root@dbf0add00eec:/opt/guildbit# flask run
 * Serving Flask app "app" (lazy loading)
 * Environment: development
 * Debug mode: on
 * Running on http://0.0.0.0:8081/ (Press CTRL+C to quit)
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 212-673-348
```

The database schema should automatically be created and ready for use.

Load `http://localhost:8081` in your browser.

See [Configuring Hosts](https://github.com/alfg/guildbit/wiki/Configuring-Hosts) on the wiki for next steps on setting up Hosts to start deploying Mumble servers.

## Admin
See: [Activating Admin](https://github.com/alfg/guildbit/wiki/Commands-and-Fixes#activating-admin)

## Translations
Translations are welcome. To add or update a translation, please add a file or update a file in [https://github.com/alfg/guildbit/tree/master/app/translations](https://github.com/alfg/guildbit/tree/master/app/translations). For more information, please read the [wiki](https://github.com/alfg/guildbit/wiki/Commands-and-Fixes#updating-translations).

## Resources
* See [The Wiki](https://github.com/alfg/guildbit/wiki/Commands-and-Fixes) for further commands available.
* [Configuration Guide](https://github.com/alfg/guildbit/wiki/Configuration-Guide)

## License

[MIT License](http://alfg.mit-license.org/) © Alfred Gutierrez
