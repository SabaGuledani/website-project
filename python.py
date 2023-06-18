from flask import Flask, render_template, request, flash, redirect, url_for
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


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    admin = db.Column(db.Boolean)


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
@app.route("/home")
def home():
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
            flash(f"Logged In!")
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


if __name__ == "__main__":
    app.run(debug=True)
