from flask import Flask
from flask_cors import CORS
from playhouse.flask_utils import FlaskDB

db_wrapper = FlaskDB()


def create_app():
    app = Flask(__name__)
    app.config.from_object('api_config')
    CORS(app)
    db_wrapper.init_app(app)

    with app.app_context():
        from . import routes
        return app
