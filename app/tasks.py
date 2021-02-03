from datetime import datetime, timedelta
from celery import Celery

from app import db
from app.models import Server
from app import murmur
import settings


app = Celery('tasks',
             broker=settings.BROKER_URL,
             backend=settings.CELERY_RESULT_BACKEND)

@app.task
def create_server(uuid, region, payload):
    """
    Celery task to create a server. Also queues delete_server task.
    @param uuid: server uuid
    @param region: server region
    @param payload: mumble server payload
    @return:
    """

    try:
        print('Creating server: ', uuid, payload)
        server_id = murmur.create_server_by_region(region, payload)

        server = Server.query.filter_by(uuid=uuid).first_or_404()
        server.mumble_instance = server_id
        server.mumble_host = murmur.get_murmur_hostname(region)
        server.status = 'active'
        db.session.add(server)
        db.session.commit()

        delete_server.apply_async([uuid], eta=server.expiration)
    except:
        import traceback
        print("ERROR creating server: %s" % uuid)
        db.session.rollback()
        traceback.print_exc()
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


if __name__ == '__main__':
    app.start()
