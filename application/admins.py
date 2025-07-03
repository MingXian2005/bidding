from application import app, db
from application.models import Users, Timer
from flask_login import current_user, login_required
from functools import wraps
from flask import render_template, request, flash, redirect, url_for, abort
from application.forms import RegistrationForm, TimerForm
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403)
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function



@app.route('/admin/register', methods=['GET', 'POST'])
@login_required
@admin_required

def admin_register():
    form = RegistrationForm()
    if form.validate_on_submit():
        IdentificationKey = form.IdentificationKey.data
        password = form.password.data
        
        # Check if IdentificationKey already exists
        existing_user = Users.query.filter_by(IdentificationKey=IdentificationKey).first()
        if existing_user:
            flash('IdentificationKey already exists. Please choose a different one.', 'danger')
            return render_template('register.html', form=form, title="Admin Registration")

        new_user = Users(IdentificationKey=IdentificationKey)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('User registered successfully!', 'success')
        return redirect(url_for('admin_register'))
    return render_template('register.html', form=form, title="Admin Registration")


@app.route('/admin/page', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_page():
    form = TimerForm()
    timer = Timer.query.order_by(Timer.id.desc()).first()
    if form.validate_on_submit():
        duration = form.duration.data  # duration in minutes
        end_time = datetime.now(ZoneInfo("Asia/Singapore")) + timedelta(minutes=duration)
        # Remove old timers if you want only one active
        Timer.query.delete()
        db.session.commit()
        timer = Timer(end_time=end_time)
        db.session.add(timer)
        db.session.commit()
        flash(f'Auction timer set for {duration} minutes.', 'success')
        return redirect(url_for('admin_page'))
    return render_template('admin_page.html', form=form, timer=timer, title="Admin Page")

@app.route('/admin/page/start', methods=['POST'])
@login_required
@admin_required
def admin_start_auction():
    # You can get duration from a form or use a default
    duration = int(request.form.get('duration', 5))  # default 5 minutes if not provided
    end_time = datetime.now(ZoneInfo("Asia/Singapore")) + timedelta(minutes=duration)
    # Remove old timers
    Timer.query.delete()
    db.session.commit()
    timer = Timer(end_time=end_time)
    db.session.add(timer)
    db.session.commit()
    flash(f'Auction started for {duration} minutes.', 'success')
    return redirect(url_for('admin_page'))