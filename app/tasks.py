from datetime import datetime, timedelta
from celery import Celery

from app import db
from app.models import Server
from app import murmur
import settings


app = Celery('tasks',
             broker=settings.BROKER_URL,
             backend=settings.CELERY_RESULT_BACKEND,
)

@app.task(bind=True, default_retry_delay=30, max_retries=3)
def create_server(self, uuid, region, payload):
    """
    Celery task to create a server. Also queues delete_server task.
    @param uuid: server uuid
    @param region: server region
    @param payload: mumble server payload
    @return:
    """

    if self.request.retries >= self.max_retries:
        server_error.apply_async([uuid]) # Send to server error queue.
        return

    try:
        print('Creating server: ', uuid)
        server_id = murmur.create_server_by_region(region, payload)

        server = Server.query.filter_by(uuid=uuid).first_or_404()
        server.mumble_instance = server_id
        server.status = 'active'
        server.created_date = datetime.utcnow()
        db.session.add(server)
        db.session.commit()

        delete_server.apply_async([uuid], eta=server.expiration)
    except Exception as exc:
        import traceback
        print("ERROR creating server: %s" % uuid)
        db.session.rollback()
        traceback.print_exc()
        raise self.retry(exc=exc, countdown=30)
    finally:
        db.session.close()

    return

@app.task
def delete_server(uuid):
    """
    Celery task to delete server. If server was extended, re-apply task for updated expiration.
    @param uuid:
    @return:
    """

    try:
        print("Running delete_server task: %s" % uuid)
        s = Server.query.filter_by(uuid=uuid).first_or_404()

        if not s:
            print("Server not found: %s" % uuid)
            return

        if s.status != "expired" and datetime.utcnow() < s.expiration:  # Is not expired?
            # Re-set task with new expiration
            print("Extend task for server: %s" % uuid)
            delete_server.apply_async([uuid], eta=s.expiration)

        elif s.status != "expired":
            # Delete mumble server and expire server
            print("Deleting server: %s" % uuid)
            s.status = 'expired'
            resp = murmur.delete_server(s.mumble_host, s.mumble_instance)
            if resp:
                db.session.commit()
                print("Deleted server: %s host: %s, id: %d" % (uuid, s.mumble_host, s.mumble_instance))
            else:
                print("ERROR deleting server: %s host: %s id: %d" % (uuid, s.mumble_host, s.mumble_instance))

        else:
            print("Server instance %s already expired." % uuid)
    except:
        import traceback
        print("ERROR deleting server: %s" % uuid)
        db.session.rollback()
        traceback.print_exc()
    finally:
        db.session.close()

    return

@app.task
def server_error(uuid):
    """
    Celery task to set server status as 'error'.
    @param uuid:
    @return:
    """

    try:
        print("Running server_error task: %s" % uuid)
        s = Server.query.filter_by(uuid=uuid).first_or_404()
        s.status = 'error'
        db.session.commit()

    except:
        import traceback
        print("ERROR setting server error: %s" % uuid)
        db.session.rollback()
        traceback.print_exc()
    finally:
        db.session.close()
    return

app.conf.update(
    task_time_limit=30,
    task_soft_time_limit=10,
    task_annotations = {
        'tasks.create_server': {'rate_limit': '10/s'}
    }
)


if __name__ == '__main__':
    app.start()
