from flask import Flask
from .extensions import db, login_manager, csrf
from .config import Config
from app.models import User


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Flask-Login user loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Flask-Login configuration
    login_manager.login_view = 'main.login'  # change if your login route is different
    login_manager.login_message_category = 'info'
        
    # Register blueprints
    from .routes.main import main
    from .routes.admin import admin
    from .routes.api import api
    
    app.register_blueprint(main)
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(api, url_prefix='/api')
    
    return app
