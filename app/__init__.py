from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
import os

app = Flask(__name__, static_folder="static")  # Set static folder to app/static
app.config.from_object(Config)  # Load configuration from Config class

# Setup for the upload folder in 'static/uploads' directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Import User model for login manager
from app.models import User  

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Import routes and models at the end to avoid circular imports
from app import routes, models
