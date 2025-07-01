from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Change this to a secure secret

# Hardcoded user data for demo
users = {
    "user1": "password1",
    "user2": "password2"
}

# Bidding project details
project = {
    "title": "Project Alpha",
    "start_price": 1000,
    "start_date": datetime(2025, 7, 1, 12, 0, 0),  # example start date/time
    "duration_minutes": 60  # bidding lasts for 60 minutes
}

bids = []  # to store submitted bids

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in users and users[username] == password:
            session["username"] = username
            return redirect(url_for("main"))
        else:
            flash("Invalid username or password")
            return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/main", methods=["GET", "POST"])
def main():
    if "username" not in session:
        return redirect(url_for("login"))

    now = datetime.utcnow()
    end_time = project["start_date"] + timedelta(minutes=project["duration_minutes"])
    time_left = end_time - now

    if time_left.total_seconds() < 0:
        time_left = timedelta(seconds=0)  # bidding ended

    if request.method == "POST":
        try:
            bid_price = float(request.form["bid_price"])
            # For simplicity: accept all bids higher than start_price
            if bid_price > project["start_price"]:
                bids.append({"user": session["username"], "price": bid_price, "time": now})
                flash(f"Bid of ${bid_price} submitted!")
            else:
                flash(f"Bid must be higher than start price (${project['start_price']})")
        except ValueError:
            flash("Invalid bid price")

    highest_bid = max([b["price"] for b in bids], default=project["start_price"])

    return render_template("main.html",
                           project=project,
                           time_left=int(time_left.total_seconds()),
                           highest_bid=highest_bid)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
