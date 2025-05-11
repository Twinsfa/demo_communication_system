# extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

db = SQLAlchemy()  # Khởi tạo db ở đây
migrate = Migrate()
jwt = JWTManager()