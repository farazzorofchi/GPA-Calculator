from flask import Flask, render_template, request, redirect

import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# app = Flask(__name__)
#
# @app.route('/')
# def index():
#   return render_template('index.html')
#
# @app.route('/about')
# def about():
#   return render_template('about.html')
#
# if __name__ == '__main__':
#   app.run(port=33507)




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

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
#db = SQL("sqlite:///Students.db")
db = SQL("sqlite:///Students.db")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    courses = db.execute("SELECT course_name, credit, score FROM courses WHERE id = :user_id", user_id=session["user_id"])
    GPA = db.execute("SELECT GPA FROM users WHERE id = :user_id", user_id=session["user_id"])


    # scores = {}
    # for course in courses:
    #     scores[course["course_name"]] = course["score"]

    GPA_Final = GPA[0]["GPA"]

    return render_template("transcript.html", courses=courses, GPA=GPA_Final)


@app.route("/course_list", methods=["GET", "POST"])
@login_required
def course_list():

    """Show history of transactions"""
    if request.method == "POST":

        db.execute("DELETE FROM courses WHERE id = :user_id", user_id=session["user_id"])
        return render_template("input.html")

    else:

        transactions = db.execute("SELECT course_name, credit, score, time FROM courses WHERE id = :user_id ORDER BY time ASC", user_id=session["user_id"])
        return render_template("course_list.html", transactions=transactions)


@app.route("/transcript", methods=["GET", "POST"])
@login_required
def transcript():
    """Show portfolio of stocks"""
    courses = db.execute("SELECT course_name, credit, score FROM courses WHERE id = :user_id", user_id=session["user_id"])
    GPA = db.execute("SELECT GPA FROM users WHERE id = :user_id", user_id=session["user_id"])

    GPA_Final = round(GPA[0]["GPA"],2)

    return render_template("transcript.html", courses=courses, GPA=GPA_Final)

@app.route("/input", methods=["GET", "POST"])
@login_required
def input():
    """Buy shares of stock"""
    if request.method == "POST":

        score = request.form.get("score")
        if (float(score) < 0) | (float(score) > 4):
            return apology("score must be a positive integer <= 4")

        if float(score)/(int(score)) != 1:
            return apology("score must be a positive integer <= 4")

        score = int(score)
        credit = request.form.get("credit")
        if (float(credit) < 0) | (float(credit) > 4):
            return apology("credit must be a positive integer")

        if float(credit)/(int(credit)) != 1:
            return apology("credit must be a positive integer")

        credit = int(credit)
        course = request.form.get("course")


        db.execute("INSERT INTO courses (id, course_name, credit, score) VALUES (:user_id, :course_name, :credit, :score)", user_id=session["user_id"], course_name=request.form.get("course"), credit=request.form.get("credit"), score=request.form.get("score"))
        current_scores = db.execute("select SUM(score*credit)/SUM(credit) as gpa FROM courses where id = :user_id GROUP BY id", user_id=session["user_id"])
        gpa =current_scores[0]["gpa"]
        db.execute("UPDATE users SET GPA = :gpa where id = :user_id", user_id=session["user_id"], gpa=gpa)

        flash("Course Added!")
        return render_template("input.html")

    else:
        return render_template("input.html")


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
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return render_template("input.html")

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



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        if not request.form.get("username"):
            return apology("Must provide username", 400)

        elif not request.form.get("password"):
            return apology("Must provide password", 400)

        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("Password do not match", 400)

        hash = generate_password_hash(request.form.get("password"))

        check_user_id = db.execute("SELECT * FROM users WHERE username = :username", username = request.form.get("username"))

        if len(check_user_id) >= 1:
            return apology("username taken", 400)

        new_user_id = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", username = request.form.get("username"), hash = hash)

        session["user_id"] = new_user_id
        flash("Registered")
        return render_template("input.html")

    else:

        return render_template("register.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

if __name__ == '__main__':
  app.run(port=33507)


