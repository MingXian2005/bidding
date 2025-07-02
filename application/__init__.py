from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from flask_login import LoginManager
from flask_socketio import SocketIO

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # For flash messages

# Setup SQLite DB URI (file 'visitors.db' in current folder)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///visitors.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
socketio = SocketIO(app)

with app.app_context():
    from .models import User, Bid
    db.create_all()
    db.session.commit()
    print('Created Database!')

#run the file routes.py
from application import routes