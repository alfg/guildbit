FROM ubuntu:18.04

EXPOSE 5000

ENV DEBIAN_FRONTEND noninteractive

# Build Python app.
RUN apt-get update && apt-get install -y python python-pip sqlite3
ADD requirements.txt /opt/requirements.txt
RUN cd /opt && pip install -r requirements.txt

# Add app with default settings.
ADD . /opt
WORKDIR /opt

CMD ["python", "manage.py", "runserver"]
