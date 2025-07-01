from application import app, db
from application.models import User
from flask import render_template, request, flash, redirect, url_for
from application.forms import RegistrationForm

@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    form = RegistrationForm()
    if form.validate_on_submit():
        IdentificationKey = form.IdentificationKey.data
        password = form.password.data
        
        # Check if IdentificationKey already exists
        existing_user = User.query.filter_by(IdentificationKey=IdentificationKey).first()
        if existing_user:
            flash('IdentificationKey already exists. Please choose a different one.', 'danger')
            return render_template('register.html', form=form, title="Admin Registration")

        new_user = User(IdentificationKey=IdentificationKey)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('User registered successfully!', 'success')
        return redirect(url_for('admin_register'))
    return render_template('register.html', form=form, title="Admin Registration")