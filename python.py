from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_session import Session
from wtforms import Form, StringField, PasswordField, validators, SubmitField
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

db = SQLAlchemy()
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.static_folder = 'static'
app.secret_key = "spookyskeletons"
db.init_app(app)
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    admin = db.Column(db.Boolean)


class Albums(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), unique=True, nullable=False)
    artist = db.Column(db.String(200), unique=True, nullable=False)
    date = db.Column(db.String(50), nullable=False)
    tags = db.Column(db.String(500), nullable=False)
    summary = db.Column(db.String, nullable=False)
    image = db.Column(db.String(200), nullable=False)


class RegistrationForm(Form):
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email Address', [validators.Length(min=6, max=35)])
    password = PasswordField('New Password', [
        validators.Length(min=8, max=30),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')
    submit = SubmitField('Go')


class LoginForm(Form):
    username = StringField('Username', [validators.Length(min=4, max=25)])
    password = PasswordField('New Password', [validators.Length(min=8, max=30)])
    submit = SubmitField('Go')


with app.app_context():
    db.create_all()


@app.route("/")
def landing():
    return redirect(url_for('home'))


@app.route("/home", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        query = request.form["search-form"]
        if query != "":
            return redirect(url_for("search", query=query))
        else:
            return redirect(url_for("browse"))

    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST" and form.validate():
        username = form.username.data
        password = form.password.data
        user = db.session.execute(db.select(User).filter_by(username=username)).scalar()
        if user is None:
            flash("User Does Not Exist")
        elif not check_password_hash(user.password, password):
            flash("Incorrect Password")
        else:
            session["username"] = user.username
            session["email"] = user.email
            session["date"] = str(user.date)[:-9]
            session["admin"] = user.admin
            return redirect(url_for("home"))
    return render_template("login.html", form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm(request.form)
    if request.method == "POST" and form.validate():
        email = form.email.data
        username = form.username.data
        password = form.password.data
        if db.session.execute(db.select(User).filter_by(username=username)).scalar() is not None:
            flash(f"Username Is Taken")
        elif db.session.execute(db.select(User).filter_by(email=email)).scalar() is not None:
            flash(f"Email Already In Use")
        else:
            user = User(email=email, username=username, password=generate_password_hash(password),
                        date=datetime.date.today(), admin=False)
            db.session.add(user)
            db.session.commit()
            flash(f"Registered!")
            return redirect(url_for("login"))
    return render_template("register.html", form=form)


@app.route("/logout")
def logout():
    for key in list(session.keys()):
        session.pop(key)
    flash("Logged Out")
    return redirect(url_for("login"))


@app.route("/browse")
def browse():
    albums = db.session.execute(db.select(Albums)).scalars()
    return render_template("browse.html", albums=albums)


@app.route("/browse/<album_title>", methods=["GET", "POST"])
def album(album_title):
    album_obj = db.session.execute(db.select(Albums).filter_by(title=album_title)).scalar()
    if request.method == "POST":
        if "username" in session:
            flash("Purchase Successful!")
        else:
            flash("Can't Purchase Without An Account!")
    return render_template("album.html", album=album_obj)


@app.route("/search=<query>")
def search(query):
    albums = Albums.query.filter(Albums.title.like(f"%{query}%") | Albums.artist.like(f"%{query}%"))

    print([i for i in albums])

    return render_template("browse.html", albums=albums)


@app.route("/about")
def about():
    return render_template("about.html")


if __name__ == "__main__":
    app.run(debug=True)
