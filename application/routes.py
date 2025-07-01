from application import app, db
from application.forms import LoginForm, RegistrationForm, BidForm
from application.models import User, Bid
from flask import render_template, request, flash, json, jsonify, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from . import admin
import os
from werkzeug.utils import secure_filename

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('bidding'))
    loginform = LoginForm()
    return render_template('login.html', form=loginform, title="Authentication")

@app.route('/auth', methods=['GET','POST'])
def auth():
    if current_user.is_authenticated:
        return redirect(url_for('bidding'))
    loginform = LoginForm()
    if loginform.validate_on_submit():
        user = User.query.filter_by(IdentificationKey=loginform.IdentificationKey.data).first()
        if user and user.check_password(loginform.password.data):
            login_user(user)
            flash('Login successful.', 'success')
            return redirect(url_for('bidding'))
        else:
            flash('Invalid Identification Key or password.', 'danger')
    return render_template('login.html', form=loginform, title="Authentication")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# Define upload folder (do this near app config)
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'application', 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Optional: show all visitors (for testing)
# @app.route('/visitors')
# @login_required
# def visitors():
#     all_visitors = Visitor.query.all()
#     return render_template('visitors.html', visitors=all_visitors)

from datetime import datetime

@app.route('/bid', methods=['GET', 'POST'])
@login_required
def bid():
    form = BidForm()
    if form.validate_on_submit():
        new_bid = Bid(amount=form.amount.data, user=current_user)
        db.session.add(new_bid)
        db.session.commit()
        flash('Your bid has been placed successfully!', 'success')
        return redirect(url_for('bidding'))
    return render_template('bid.html', form=form)

# import os
# print("TEMPLATE DIR:", os.getcwd(), flush=True)

from flask import render_template
from application import app

@app.route('/bidding')
def bidding():
    # For now, let's use some dummy bids
    from datetime import datetime

    class DummyUser:
        IdentificationKey = "test_user"

    class DummyBid:
        amount = 123.45
        timestamp = datetime.utcnow()
        user = DummyUser()

    bids = [DummyBid(), DummyBid()]

    return render_template('bidding.html', bids=bids)
