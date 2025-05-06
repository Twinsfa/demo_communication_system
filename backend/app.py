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
    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.users import users_bp
    from routes.messages import messages_bp
    from routes.announcements import announcements_bp
    from routes.forms import forms_bp
    from routes.grades import grades_bp
    from routes.rewards import rewards_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(messages_bp, url_prefix='/api/messages')
    app.register_blueprint(announcements_bp, url_prefix='/api/announcements')
    app.register_blueprint(forms_bp, url_prefix='/api/forms')
    app.register_blueprint(grades_bp, url_prefix='/api/grades')
    app.register_blueprint(rewards_bp, url_prefix='/api/rewards')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True) 