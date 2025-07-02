from application import app, db, socketio
from application.forms import LoginForm, RegistrationForm, BidForm
from application.models import User, Bid
from flask import render_template, request, flash, json, jsonify, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from . import admin
import os
from werkzeug.utils import secure_filename
from sqlalchemy import asc
from datetime import datetime, timedelta, timezone


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

@app.route('/bid', methods=['GET', 'POST'])
@login_required
def bid():
    global auction_end_time
    form = BidForm()
    now = datetime.now(timezone.utc)

    # If auction hasn't started, show full duration and mark as not started
    auction_started = auction_end_time is not None
    if not auction_started:
        time_left = AUCTION_DURATION
        auction_over = False
    else:
        time_left = int((auction_end_time - now).total_seconds())
        auction_over = time_left <= 0

    if form.validate_on_submit() and not auction_over:
        # Start auction on first bid
        if not auction_started:
            auction_end_time = now + timedelta(seconds=AUCTION_DURATION)
            auction_started = True
            time_left = AUCTION_DURATION
        else:
            # Only add extension if time_left <= 2 minutes (120 seconds)
            if time_left <= 120:
                auction_end_time += timedelta(seconds=AUCTION_EXTENSION)
        new_bid = Bid(amount=form.amount.data, user=current_user)
        db.session.add(new_bid)
        db.session.commit()
        socketio.emit('new_bid', {
            'IdentificationKey': new_bid.user.IdentificationKey,
            'amount': new_bid.amount,
            'timestamp': new_bid.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })
        flash('Your bid has been placed successfully!', 'success')
        return redirect(url_for('bidding'))
    elif form.is_submitted() and auction_over:
        flash('Bidding has ended. You cannot place a bid.', 'danger')

    # Recalculate time_left for rendering
    if not auction_started:
        time_left = AUCTION_DURATION
        auction_over = False
    else:
        time_left = int((auction_end_time - datetime.now(timezone.utc)).total_seconds())
        auction_over = time_left <= 0

    return render_template(
        'bid.html',
        form=form,
        time_left=max(time_left, 0),
        auction_over=auction_over,
        auction_started=auction_started,
        AUCTION_DURATION=AUCTION_DURATION  # <-- add this line
    )

# import os
# print("TEMPLATE DIR:", os.getcwd(), flush=True)

from flask import render_template
from application import app

@app.route('/bidding', methods=['GET'])
def bidding():
    bids = Bid.query.order_by(asc(Bid.amount)).all()  # Replace `amount` with your column
    return render_template('bidding.html', bids=bids)

# Set auction end time (example: 5 minutes from server start)
AUCTION_DURATION = 1 * 2 * 60  # 5 minutes in seconds
AUCTION_EXTENSION = 60     # 60 seconds per bid

auction_end_time = None    # Will be set on first bid
