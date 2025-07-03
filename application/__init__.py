from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from flask_login import LoginManager
from flask_socketio import SocketIO
from dotenv import load_dotenv
# import psycopg2


# Load .env variables
load_dotenv()

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # For flash messages

# Setup SQLite DB URI (file 'visitors.db' in current folder)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
socketio = SocketIO(app, async_mode='eventlet')

with app.app_context():
    from .models import Users, Bid, Timer
    db.drop_all()
    db.create_all()

    # Create admin user
    if not Users.query.filter_by(IdentificationKey='admin').first():
        admin = Users(IdentificationKey='admin')
        admin.set_password('admin')
        db.session.add(admin)

    db.session.commit()
    print('Created Database!')

#run the file routes.py
from application import routes
from application import admins
