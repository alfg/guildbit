from app import app, manager
import settings

if __name__ == '__main__':
    # app.run(debug=settings.APP_DEBUG, host=settings.APP_HOST, port=settings.APP_PORT)
    manager.run()

