import logging
logging.basicConfig(level=logging.DEBUG)

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import timedelta
import os

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-please-change')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///school_communication.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    
    # Initialize extensions with app
    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:8000", "http://127.0.0.1:8000"]}}, supports_credentials=True)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.users import users_bp
    from routes.messages import messages_bp
    from routes.notifications import notifications_bp
    from routes.forms import forms_bp
    from routes.evaluations import evaluations_bp
    from routes.rewards import rewards_bp, init_rewards_table
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(messages_bp, url_prefix='/api/messages')
    app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
    app.register_blueprint(forms_bp, url_prefix='/api/forms')
    app.register_blueprint(evaluations_bp, url_prefix='/api/evaluations')
    app.register_blueprint(rewards_bp, url_prefix='/api/rewards')


    @app.cli.command("init-db")
    def init_db():
        """Khởi tạo cơ sở dữ liệu."""
        db.create_all()
        print("✅ Database has been initialized.")

    @app.cli.command("init-demo")
    def init_demo():
        """Khởi tạo dữ liệu demo."""
        from init_data import init_demo_data
        init_demo_data()
        init_rewards_table()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000) 