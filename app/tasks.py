from datetime import datetime, timedelta
from celery import Celery

from app import db
from app.models import Server
import murmur
import settings


app = Celery('tasks',
             broker=settings.BROKER_URL,
             backend=settings.CELERY_RESULT_BACKEND)


@app.task
def delete_server(uuid):
    """
    Celery task to delete server. If server was extended, re-apply task for updated expiration.
    @param uuid:
    @return:
    """
    s = Server.query.filter_by(uuid=uuid).first_or_404()

    if s.status != "expired" and datetime.utcnow() < s.expiration:  # Is not expired?

        # Re-set task with new expiration
        delete_server.apply_async([uuid], eta=s.expiration)
        print "Extend task for server instance: %s" % id

    elif s.status != "expired":
        # Delete mumble server and expire server
        s.status = 'expired'
        murmur.delete_server(s.mumble_host, s.mumble_instance)
        db.session.commit()
        print "Deleting server instance: %s" % id

    else:
        print "Server instance %s already expired." % id

    return


app.conf.update(
    CELERY_TASK_RESULT_EXPIRES=3600,
)


if __name__ == '__main__':
    app.start()
