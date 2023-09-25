from flask import Flask, render_template, url_for, flash
from forms import RegistrationForm, LoginForm

app = Flask(__name__)
app.config['SECRET_KEY'] = "3022ca0d1572079ce80786510f474801"
@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/register")
def register():
    form = RegistrationForm()
    flash("This is a flashed message", 'error')
    return render_template("register.html", title = "Register", form=form)

@app.route("/login")
def login():
    form = LoginForm()
    return render_template("login.html", form=form)

if __name__ == "__main__":
    app.run(debug=True)