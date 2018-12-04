import os

from cs50 import SQL
from datetime import datetime # Imported for histories
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks --- TODO """
   # Current user
    users = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id = session["user_id"])
    stocks = db.execute("SELECT symbol, SUM(shares) as total_shares FROM portfolio WHERE user_id = :user_id GROUP BY symbol HAVING total_shares > 0 ", user_id=session["user_id"])

    quotes = {}

    for stock in stocks:
        quotes[stock["symbol"]] = lookup(stock["symbol"])


    cash_remaining = users[0]["cash"]
    total = cash_remaining

    return render_template("index.html", quotes=quotes, stocks=stocks,  total=total, cash_remaining=cash_remaining)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock --- TODO """
    if request.method == "GET":
        return render_template("buy.html")

    else:
        # Proper symbol?
        quote = lookup(request.form.get("symbol"))
        if not quote:
            return apology("Invalid symbol", 400)

        # Positive int for num of shares?
        try:
            shares = int(request.form.get("shares"))
        except:
            return apology("Shares must be a positive number", 400)

        # Did the user request 0 shares?
        if shares <= 0:
            return apology("Cant buy less than or 0 shares", 400)

        # Select user
        rows = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"])

        # Users $$
        cash_remaining = rows[0]["cash"]
        per_share = quote["price"]

        # Calculate price of requested shares
        total_price = per_share * shares

        if total_price > cash_remaining:
            return apology("Insufficient funds! :( ")


        # Updates histor and portfolio
        db.execute("UPDATE users SET cash = cash - :price WHERE id = :user_id", price = total_price, user_id=session["user_id"])
        db.execute("INSERT INTO portfolio (user_id, symbol, name, shares, per_share) VALUES(:user_id, :symbol, :name, :shares, :price)", \
                        user_id=session["user_id"], symbol=quote["symbol"], name=quote["name"], shares=int(request.form.get("shares")), price=per_share )

        flash("Ka-Ching! Bought")

        return redirect(url_for("index"))

@app.route("/history")
@login_required
def history():
    """Show history of transactions --- TODO """

    trans = db.execute("SELECT symbol, name, shares, per_share, timeStamp FROM portfolio WHERE user_id = :user_id ORDER BY timeStamp", user_id=session["user_id"])

    return render_template("history.html", trans=trans)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect(url_for("index"))

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote. --- TODO """
    if request.method == "POST":
        rows = lookup(request.form.get("symbol"))

        if not rows:
            return apology("Invalid symbol")

        return render_template("quoted.html", stock=rows)

    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user --- TODO """

    if request.method == "POST":

        # Was username submitted?
        if not request.form.get("username"):
            return apology("Provide a valid username")

        # Was password submitted?
        elif not request.form.get("password"):
            return apology("Provide a valid password")

        # Ensure password and verified password is the same
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords don't match")

        # Insert the new user into users, storing the hash of the user's password
        result = db.execute("INSERT INTO users (username, hash) \
                             VALUES (:username, :hash)", \
                             username=request.form.get("username"), \
                             hash=generate_password_hash(request.form.get("password")))

        if not result:
            return apology("Username already exists")

        # remember which user has logged in
        session['user_id'] = result

        # redirect user to home page
        return redirect(url_for("index"))

    else:
        return render_template("register.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock --- TODO """
    if request.method == "POST":

        symbol = lookup(request.form.get("symbol"))

        # ensure proper symbol
        if not symbol:
                return apology("Invalid Symbol", 400)

        # Positive number of shares?
        try:
            shares = int(request.form.get("shares"))
        except:
            return apology("Shares must be a positive number!", 400)

        # Does the user have enough shares?
        stock = db.execute("SELECT SUM(shares) as total_shares FROM portfolio WHERE user_id = :user_id and symbol = :symbol GROUP BY symbol",\
                            user_id = session["user_id"], symbol = request.form.get("symbol"))

        # Shares must be more than 0
        if shares <= 0:
            return apology("0 is not a valid number of shares!", 400)


        # Select the user's cash
        rows = db.execute("SELECT cash FROM users WHERE id = :id", id = session["user_id"])

        # Calculate user's cash
        remaining = rows[0]["cash"]
        per_share = symbol["price"]

        total_price = per_share * shares



        # Updates for sale
        db.execute("UPDATE users SET cash = cash + :price WHERE id = :user_id", price = total_price, user_id = session["user_id"])
        db.execute("INSERT INTO portfolio (user_id, symbol, name, shares, per_share) \
                    VALUES (:user_id, :symbol, :name, :shares, :price)",\
                    user_id = session["user_id"], symbol = request.form.get("symbol"), name=symbol["name"], shares=-shares, price= per_share )

        # Update user shares
        user_shares = db.execute("SELECT shares FROM portfolio WHERE user_id=:user_id AND symbol=:symbol", user_id=session["user_id"], symbol=symbol["symbol"] )#monitor

        if not user_shares or int(user_shares[0]["shares"]) < shares:
            return apology("Not enough shares")



        flash("Sold!")

        return redirect(url_for("index"))

    else:
        stocks = db.execute("SELECT symbol, SUM(shares) as total_shares FROM portfolio WHERE user_id = :user_id GROUP BY symbol HAVING total_shares > 0", user_id = session["user_id"])

        return render_template("sell.html", stocks=stocks)


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
