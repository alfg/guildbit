from celery import Celery
import requests
import settings

app = Celery('tasks',
             broker=settings.BROKER_URL,
             backend=settings.CELERY_RESULT_BACKEND)


@app.task
def something():
    print 'test'
    return

@app.task
def delete_server(id):
    r = requests.delete("%s/api/v1/servers/%i" % (settings.MURMUR_REST_HOST, id))
    print "Deleting server instance: %s" % id
    return


app.conf.update(
    CELERY_TASK_RESULT_EXPIRES=3600,
)

if __name__ == '__main__':
    app.start()
