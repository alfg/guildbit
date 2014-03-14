from celery import Celery

from app import db
from app.models import Server
from murmur import delete_server
import settings

app = Celery('tasks',
             broker=settings.BROKER_URL,
             backend=settings.CELERY_RESULT_BACKEND)


@app.task
def delete_server(uuid):
    s = Server.query.filter_by(uuid=uuid).first_or_404()
    s.status = 'expired'

    # Delete the server via Murmur
    delete_server(s.mumble_host, s.mumble_instance)
    db.session.commit()
    print "Deleting server instance: %s" % id
    return


app.conf.update(
    CELERY_TASK_RESULT_EXPIRES=3600,
)

if __name__ == '__main__':
    app.start()
