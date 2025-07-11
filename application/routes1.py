from application import app, db, socketio
from application.forms import LoginForm, RegistrationForm, BidForm
from application.models import Users, Bid, Timer, Initials
from flask import render_template, request, flash, json, jsonify, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from . import admin
import os
from werkzeug.utils import secure_filename
from sqlalchemy import asc, func, desc
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

################################################################################################
#homepage
################################################################################################

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('bid'))
    loginform = LoginForm()
    return render_template('login.html', form=loginform, title="Authentication")

################################################################################################
#auth / login
################################################################################################

@app.route('/auth', methods=['GET','POST'])
def auth():
    if current_user.is_authenticated:
        return redirect(url_for('bid'))
    loginform = LoginForm()
    if loginform.validate_on_submit():
        user = Users.query.filter_by(IdentificationKey=loginform.IdentificationKey.data).first()
        if user and user.check_password(loginform.password.data):
            login_user(user)
            flash('Login successful.', 'success')
            return redirect(url_for('bid'))
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
    if current_user.is_blocked:
        return redirect(url_for('bidding'))
    
    form = BidForm()
    now = datetime.now(ZoneInfo("Asia/Singapore"))
    AUCTION_EXTENSION = 60

    auction_started = False
    # Fetch latest timer
    timer = Timer.query.order_by(Timer.id.desc()).first()
    end_time_iso = timer.end_time.isoformat() if timer and timer.end_time else None
    if timer is not None:
        auction_started = True
    else:
        auction_started = False

    auction_over = False
    auction_end_time = None

    # Latest bid done by the user
    latest_bid = Bid.query.filter_by(user_id=current_user.id).order_by(Bid.timestamp.desc()).first()

    if auction_started == True:
        if timer.end_time is not None:
            auction_end_time = timer.end_time
            # Ensure timezone awareness
            # auction_end_time = auction_end_time.replace(tzinfo=ZoneInfo("Asia/Singapore"))
            auction_end_time = auction_end_time.replace(tzinfo=timezone.utc)
            auction_end_time = auction_end_time.astimezone(ZoneInfo("Asia/Singapore"))
            time_left = int((auction_end_time - now).total_seconds())
            if time_left <= 0:
                auction_over = True
            else:
                auction_over = False
        else:
            time_left = 0
        #Set auction_over to True if time_left is less than or equal to zero — otherwise, set it to False.
    else:
        time_left = 0  # default if no timer exists

    print(auction_end_time, "auction_end_time, 1")
    print(now, "now, 1")
    print(time_left, "time_left, 1")

    # Get current lowest bid
    lowest_bid = db.session.query(Bid).order_by(Bid.amount.asc()).first()
    lowest_bid_amount = lowest_bid.amount if lowest_bid else None 

    # Get decrement value
    decrement = db.session.query(Initials).order_by(Initials.BidDecrement).first()
    Decrement = decrement.BidDecrement if decrement else 0


    # Get initial bid value
    Starting_price = db.session.query(Initials).order_by(Initials.StartingBid).first()
    STARTING_PRICE = Starting_price.StartingBid if Starting_price else 1000

    # Get the value you to add into form
    if lowest_bid_amount is not None and lowest_bid_amount > 0:
        min_bid_amount = lowest_bid_amount - Decrement
    else:
        min_bid_amount = STARTING_PRICE - Decrement # or some fallback

    # Get max bid you could
    if lowest_bid_amount is not None and lowest_bid_amount > 0:
        max_bid_amount = lowest_bid_amount * 0.20
    else:
        max_bid_amount = STARTING_PRICE * 0.20  # fallback if no bids yet

    # Subquery: get the latest bid timestamp for each user
    latest_bids_subq = (
        db.session.query(
            Bid.user_id,
            func.max(Bid.timestamp).label('max_timestamp')
        )
        .group_by(Bid.user_id)
        .subquery()
    )

    # Join to get the actual latest bid for each user
    latest_bids = (
        db.session.query(Bid)
        .join(latest_bids_subq, (Bid.user_id == latest_bids_subq.c.user_id) & (Bid.timestamp == latest_bids_subq.c.max_timestamp))
        .order_by(Bid.amount.asc())
        .all()
    )

    # Build a ranking dict: user_id -> rank
    ranking = {}
    for idx, bid in enumerate(latest_bids, start=1):
        ranking[bid.user_id] = idx

    # Get current user's rank (if they have a bid)
    user_rank = ranking.get(current_user.id)


    if form.validate_on_submit() and auction_over == False:
        bid_value = form.amount.data

        if bid_value >= STARTING_PRICE:
            flash(f'Your bid must be LOWER than the starting price (S$ {STARTING_PRICE:.2f}).', 'danger')
        elif bid_value > STARTING_PRICE - Decrement: 
            flash(f'Your bid must be LOWER than the minimum bid decrement (S$ {Decrement:.2f}).', 'danger')
        elif lowest_bid_amount is not None and bid_value > lowest_bid_amount: 
            flash(f'Your bid must be LOWER than the current lowest bid (S$ {lowest_bid_amount:.2f}).', 'danger')
        elif lowest_bid_amount is not None and bid_value > lowest_bid_amount - Decrement: 
            flash(f'Your bid must be LOWER than the minimum bid decrement (S$ {Decrement:.2f}).', 'danger')
        elif bid_value < 0.01:
            flash('Your bid must be at least S$ 0.01.', 'danger')
        elif auction_end_time is None:
            flash('No active auction yet.', 'danger')
        elif bid_value < max_bid_amount:
            flash(f'Your bid must not exceed 20% of the lowest bid (S$ {max_bid_amount:.2f}).', 'danger')    
        else:
            # Extend time if <= 2 minutes left
            if time_left <= 120:
                auction_end_time += timedelta(seconds=AUCTION_EXTENSION)
                timer.end_time = auction_end_time
                db.session.add(timer)
                socketio.emit('timer_extended', {'end_time': auction_end_time.astimezone(timezone.utc).isoformat()})

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

    elif form.is_submitted() and auction_over:
        flash('Bidding has ended. You cannot place a bid.', 'danger')


    if auction_started == True:
        if timer.end_time is not None:
            auction_end_time = timer.end_time
            # Ensure timezone awareness
            auction_end_time = auction_end_time.replace(tzinfo=timezone.utc)
            auction_end_time = auction_end_time.astimezone(ZoneInfo("Asia/Singapore"))
            time_left = int((auction_end_time - now).total_seconds())
            auction_over = time_left <= 0
        else:
            time_left = 0
        #Set auction_over to True if time_left is less than or equal to zero — otherwise, set it to False.
    else:
        time_left = 0  # default if no timer exists
    
    bids = Bid.query.order_by(asc(Bid.amount)).all()

    return render_template(
        'bid.html',
        form=form,
        time_left=max(time_left, 0),
        auction_over=auction_over,
        auction_started=auction_started,
        starting_price=STARTING_PRICE,
        timer=timer,
        # end_time_iso=end_time_iso,
        latest_bid=latest_bid,
        user_rank=user_rank,
        ranking=ranking,
        min_bid_amount=min_bid_amount,
        decrement=Decrement,
        max_bid_amount=max_bid_amount,
        lowest_bidding = lowest_bid_amount,
        bids=bids
    )

################################################################################################
# bidding history
################################################################################################
from flask import render_template
from application import app

@app.route('/bidding', methods=['GET'])
@login_required
def bidding():
    bids = Bid.query.order_by(asc(Bid.amount)).all()  # Replace `amount` with your column
    timer = Timer.query.order_by(Timer.id.desc()).first()
    # end_time_iso = timer.end_time.isoformat() if timer and timer.end_time else None
    if timer and timer.end_time:
        end_time_iso_utc = timer.end_time.replace(tzinfo=ZoneInfo('UTC'))
        end_time_iso = end_time_iso_utc.astimezone(ZoneInfo("Asia/Singapore"))
    else:
         end_time_iso = None

    # Convert bid timestamps from UTC to SG
    for bid in bids:
        if bid.timestamp:
            utc_ts = bid.timestamp.replace(tzinfo=ZoneInfo('UTC'))
            bid.timestamp_sg = utc_ts.astimezone(ZoneInfo("Asia/Singapore"))

    return render_template('bidding.html', bids=bids, timer=timer, end_time_iso=end_time_iso)

##############################################################################################
@app.route('/reset', methods=['POST', 'GET'])
@login_required
def reset():
    # Optional: Only allow admin to reset
    if not current_user.is_admin:
        flash('Only admin can reset the auction.', 'danger')
        return redirect(url_for('bid'))

    # Delete all bids
    Bid.query.delete()
    # Delete all timers
    Timer.query.delete()
    db.session.commit()
    flash('All bids and auction timer have been reset.', 'success')
    return redirect(url_for('bid'))
