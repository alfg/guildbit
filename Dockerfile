FROM ubuntu:20.04

WORKDIR /opt/guildbit

ENV FLASK_APP=app
ENV DEBIAN_FRONTEND noninteractive
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# Install system dependencies.
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-psycopg2 \
    sqlite3

# Install supervisor to system.
RUN pip3 install supervisor

# Create virtual env and setup Python app.
ADD requirements.txt /opt/guildbit/requirements.txt
RUN python3 -m venv --system-site-packages venv && \
    ./venv/bin/pip3 install -r requirements.txt

# Add config files.
ADD ./etc/supervisord.conf /etc/supervisor/supervisord.conf

# Add app.
ADD . /opt/guildbit

# Compile translation files from PO to MO.
RUN venv/bin/pybabel compile -f -d app/translations

EXPOSE 8081

# Set version from CI build.
ARG BUILD_VERSION
ENV BUILD_VERSION=$DOCKER_TAG

CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]
