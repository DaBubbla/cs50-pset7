import os

from cs50 import SQL
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

cash = 0 # User's cash? Testing location


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks --- TODO """
    return apology("TODO")



@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():

    """Buy shares of stock --- TODO """
    if request.method =="GET":
        return render_template("buy.html")

    else:
        stock = lookup(request.form.get("symbol"))
        if not stock:
            return apology("Invalid symbol")

        # Positive int for num of shares?
        try:
            shares = int(request.form.get("shares"))
            if shares < 0:
                return apology("Shares must be a positive number")
        except:
            return apology("Shares must be a positive number")

        # Select user's cash
        usersCash = db.execute("SELECT cash FROM users WHERE id = :id", id=session["user_id"])

        # Is there enough $$ to buy?
        if not usersCash or float(usersCash[0]["cash"]) < stock["price"] * shares:
            return apology("Insufficient funds! :(")

        # Update history
        db.execute("INSERT INTO histories (symbol, shares, price, id) \
        VALUES(:symbol, :shares, :price, :id)",\
        symbol=stock["symbol"], shares=shares, price=usd(stock["price"]), id=session["user_id"] )

        # Update user's cash
        checkout = usd(stock["price"])
        cashUpdate = db.execute("UPDATE users SET cash = cash - checkout WHERE id = :id", id=session['user_id'])


@app.route("/history")
@login_required
def history():
    """Show history of transactions --- TODO """
    return apology("TODO")


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
        return redirect("index")

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
        #returns quote.name... ???

        if not rows:
            return apology("Invalid symbol")
        else:
            return render_template("quoted.html")#, name='symbol' might use this later?

    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user --- TODO """
    # Check for usage
    if request.method == "POST":

        # Was username submitted?
        if not request.method("username"):
            return apology("Provide a valid username")

        # Was password submitted?
        elif not request.method("password"):
            return apology("Provide a valid password")

        # Ensure password and verified password is the same
        elif request.form.get("password") != request.form.get("quote"):
            return apology("Passwords don't match")

        # Insert the new user into users, storing the hash of the user's password
        result = db.execute("INSERT INTO users (id, name, hash),\
                             VALUES (:username, :hash)",\
                             username = request.form.get("username"),\
                             hash = generate_password_hash(request.form.get("password")))

        if not result:
            return apology("Username already exists")


        # remember which user has logged in
        session['user_id'] = result

        # redirect user to home page
        return redirect(url_for("/index"))

    else:
        return render_template("/register.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock --- TODO """
    return apology("TODO")


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
