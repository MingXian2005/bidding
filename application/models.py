from application import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    IdentificationKey = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Visitor model
class Visitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    contact_number = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100))
    purpose = db.Column(db.Text)
    host = db.Column(db.String(100))
    visit_date = db.Column(db.String(20), nullable=False)  # Store as string (YYYY-MM-DD)
    visit_time = db.Column(db.String(10))
    id_type = db.Column(db.String(50))
    id_number = db.Column(db.String(100))
    document_filename = db.Column(db.String(200))