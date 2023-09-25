from flask import Flask, render_template, url_for, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from forms import RegistrationForm, LoginForm


app = Flask(__name__)
app.config['SECRET_KEY'] = "3022ca0d1572079ce80786510f474801"
app.config['SQLALCHEMY_DATABASE_URI'] = "qslite:///site.db"


@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/register", methods = ['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        flash(f'Account successfully created.')
        return redirect(url_for('home'))

    return render_template("register.html", title = "Register", form=form)

@app.route("/login", methods = ['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash(f'You have successfully logged in.')
        return redirect(url_for('home'))
    return render_template("login.html", form=form)

if __name__ == "__main__":
    app.run(debug=True)