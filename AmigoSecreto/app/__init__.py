from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO
from datetime import datetime
from flasgger import Swagger
import os
from dotenv import load_dotenv


db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
socketio = SocketIO()
migrate = Migrate()
load_dotenv()  


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')


    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app)
    migrate.init_app(app, db)



    login_manager.login_view = 'main.login'
    login_manager.login_message_category = 'info'


    swagger_template_path = os.path.join(os.path.dirname(__file__), 'swagger_config.yaml')
    swagger = Swagger(app, template_file=swagger_template_path)


    with app.app_context():
        from .models import User, Group, Participant, Gift, Message
        db.create_all()


    from .routes import main
    app.register_blueprint(main)


    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))


    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}
    
    return app
