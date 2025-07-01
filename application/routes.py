from application import app, db
from application.models import User, Visitor
from datetime import datetime
from application.forms import LoginForm, RegistrationForm
from flask import render_template, request, flash, json, jsonify, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from . import admin
import os
from werkzeug.utils import secure_filename

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('prereg'))
    loginform = LoginForm()
    return render_template('login.html', form=loginform, title="Authentication")

@app.route('/auth', methods=['GET','POST'])
def auth():
    if current_user.is_authenticated:
        return redirect(url_for('prereg'))
    loginform = LoginForm()
    if loginform.validate_on_submit():
        user = User.query.filter_by(IdentificationKey=loginform.IdentificationKey.data).first()
        if user and user.check_password(loginform.password.data):
            login_user(user)
            flash('Login successful.', 'success')
            return redirect(url_for('prereg'))
        else:
            flash('Invalid Identification Key or password.', 'danger')
    return render_template('login.html', form=loginform, title="Authentication")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/reg')
@login_required
def prereg():
    return render_template('pre_registration.html')

# Define upload folder (do this near app config)
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'application', 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/submit', methods=['POST'])
@login_required
def submit():
    # Get form data
    full_name = request.form.get('full_name')
    contact_number = request.form.get('contact_number')
    email = request.form.get('email')
    company = request.form.get('company')
    purpose = request.form.get('purpose')
    host = request.form.get('host')
    visit_date = request.form.get('visit_date')
    visit_time = request.form.get('visit_time')
    id_type = request.form.get('id_type')
    id_number = request.form.get('id_number')
    uploaded_file = request.files.get('document')

    # Simple validation
    if not full_name or not contact_number or not email or not visit_date:
        flash('Please fill in all required fields (Name, Contact, Email, Visit Date)')
        return redirect(url_for('prereg'))

    filename = None
    if uploaded_file and uploaded_file.filename != '':
        filename = secure_filename(uploaded_file.filename)
        uploaded_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    # Create Visitor object
    visitor = Visitor(
        full_name=full_name,
        contact_number=contact_number,
        email=email,
        company=company,
        purpose=purpose,
        host=host,
        visit_date=visit_date,
        visit_time=visit_time,
        id_type=id_type,
        id_number=id_number,
        document_filename=filename
    )

    # Save to DB
    db.session.add(visitor)
    db.session.commit()

    flash('Pre-registration successful! Your visit details have been saved.')
    return redirect(url_for('prereg'))

# Optional: show all visitors (for testing)
@app.route('/visitors')
@login_required
def visitors():
    all_visitors = Visitor.query.all()
    return render_template('visitors.html', visitors=all_visitors)