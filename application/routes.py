from application import app, db, socketio
from application.forms import LoginForm, RegistrationForm, BidForm
from application.models import User, Bid, Timer
from flask import render_template, request, flash, json, jsonify, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from . import admin
import os
from werkzeug.utils import secure_filename
from sqlalchemy import asc
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

## Incase of directory issue from flask
# import os
# print("TEMPLATE DIR:", os.getcwd(), flush=True)

# Define upload folder (do this near app config)
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'application', 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

################################################################################################
#homepage
################################################################################################

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('bidding'))
    loginform = LoginForm()
    return render_template('login.html', form=loginform, title="Authentication")

################################################################################################
#auth / login
################################################################################################

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

################################################################################################
#logout
################################################################################################

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

################################################################################################
# placing bid
################################################################################################

@app.route('/bid', methods=['GET', 'POST'])
@login_required
def bid():
    form = BidForm()
    now = datetime.now(ZoneInfo("Asia/Singapore"))

    # Fetch latest timer
    timer = Timer.query.order_by(Timer.id.desc()).first()
    auction_started = timer is not None
    auction_over = False
    auction_end_time = None

    if auction_started:
        auction_end_time = timer.end_time
        # Ensure timezone awareness
        if auction_end_time and auction_end_time.tzinfo is None:
            auction_end_time = auction_end_time.replace(tzinfo=ZoneInfo("Asia/Singapore"))
        time_left = int((auction_end_time - now).total_seconds())
        auction_over = time_left <= 0
    else:
        time_left = AUCTION_DURATION  # default if no timer exists

    # Get current lowest bid
    lowest_bid = db.session.query(Bid).order_by(Bid.amount.asc()).first()
    lowest_bid_amount = lowest_bid.amount if lowest_bid else None

    if form.validate_on_submit() and not auction_over:
        bid_value = form.amount.data

        if bid_value >= STARTING_PRICE:
            flash(f'Your bid must be LOWER than the starting price (S$ {STARTING_PRICE:.2f}).', 'danger')
        elif lowest_bid_amount is not None and bid_value >= lowest_bid_amount:
            flash(f'Your bid must be LOWER than the current lowest bid (S$ {lowest_bid_amount:.2f}).', 'danger')
        elif bid_value < 0.01:
            flash('Your bid must be at least S$ 0.01.', 'danger')
        else:
            # Start auction on first bid
            if not auction_started:
                auction_end_time = now + timedelta(seconds=AUCTION_DURATION)
                timer = Timer(end_time=auction_end_time)
                db.session.add(timer)
            else:
                # Extend time if <= 2 minutes left
                if time_left <= 120:
                    auction_end_time += timedelta(seconds=AUCTION_EXTENSION)
                    timer.end_time = auction_end_time

            # Save bid
            new_bid = Bid(amount=bid_value, user=current_user)
            db.session.add(new_bid)
            db.session.commit()

            # Emit real-time update
            socketio.emit('new_bid', {
                'IdentificationKey': new_bid.user.IdentificationKey,
                'amount': new_bid.amount,
                'timestamp': new_bid.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            })

            flash('Your bid has been placed successfully!', 'success')
            return redirect(url_for('bidding'))

    elif form.is_submitted() and auction_over:
        flash('Bidding has ended. You cannot place a bid.', 'danger')

    # Final time_left (recalculate to reflect updated timer)
    if auction_end_time:
        time_left = int((auction_end_time - datetime.now(ZoneInfo("Asia/Singapore"))).total_seconds())
        auction_over = time_left <= 0
    else:
        time_left = AUCTION_DURATION

    return render_template(
        'bid.html',
        form=form,
        time_left=max(time_left, 0),
        auction_over=auction_over,
        auction_started=auction_started,
        AUCTION_DURATION=AUCTION_DURATION,
        starting_price=STARTING_PRICE
    )

################################################################################################
# bidding history
################################################################################################
from flask import render_template
from application import app

@app.route('/bidding', methods=['GET'])
def bidding():
    bids = Bid.query.order_by(asc(Bid.amount)).all()  # Replace `amount` with your column
    timer = Timer.query.order_by(Timer.id.desc()).first()
    return render_template('bidding.html', bids=bids, timer=timer)

# Set auction end time (example: 5 minutes from server start)
AUCTION_DURATION = 1 * 2 * 60  # 5 minutes in seconds
AUCTION_EXTENSION = 60     # 60 seconds per bid
STARTING_PRICE = 100.00  # or whatever your starting price is

auction_end_time = None    # Will be set on first bid
