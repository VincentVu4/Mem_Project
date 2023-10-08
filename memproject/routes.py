import os
import secrets
from PIL import Image
from flask import Flask, render_template, url_for, flash, redirect, request, abort
from memproject import app, db, bcrypt, mail
from memproject.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, ResetPasswordForm, RequestResetForm
from memproject.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message

posts = [
    {
        'author': 'Corey Schafer',
        'title': 'Blog Post 1',
        'content': 'First post content',
        'date_posted': 'April 20, 2018'
    },
    {
        'author': 'Jane Doe',
        'title': 'Blog Post 2',
        'content': 'Second post content',
        'date_posted': 'April 21, 2018'
    }
]


@app.route("/")
@app.route("/home")
def home():
    page = request.args.get('page', 1, type = int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page = page, per_page = 5)
    return render_template("home.html", posts = posts)

@app.route("/register", methods = ['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username = form.username.data, email = form.email.data, password = hashed_password)

        db.session.add(user)
        db.session.commit()
        flash(f'Account successfully created.', "success")
        return redirect(url_for('login'))

    return render_template("register.html", title = "Register", form=form)

@app.route("/login", methods = ['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash(f'Login unsuccessful. Please check your email and password.', "danger")
    return render_template("login.html", title = "Login", form=form)

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile-pics', picture_fn)
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn

@app.route("/account", methods = ['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash("Your account has been updated!", "success")
    elif request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename = 'profile-pics/' + current_user.image_file)
    return render_template("account.html", title = "Account", image_file = image_file, form = form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/new_post", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            post = Post(title=form.title.data, content=form.content.data, image_file_post = picture_file, author=current_user)
            db.session.add(post)
            db.session.commit()
            flash('Your post has been created!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Your post has not been created!', 'danger')
    return render_template('create_post.html', title='New Post', form=form, legend= "New Post")

@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template("post.html", title = post.title, post = post)

@app.route("/post/<int:post_id>/update", methods = ['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        if form.submit.data:
            if form.picture.data:
                picture_file = save_picture(form.picture.data)
                post.image_file_post = picture_file
            post.title = form.title.data
            post.content = form.content.data
            db.session.commit()
            flash("Your post has been updated!", "success")
            return redirect(url_for("post", post_id = post.id))
        elif form.delete.data:
            return redirect(url_for('delete_post', post_id = post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template("create_post.html", title = 'Update Post', form = form, legend="Update Post")

@app.route("/post/<int:post_id>/delete", methods = ['GET', 'POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash("Your post has sucessfully been deleted!", "info")
    return redirect(url_for("home"))


def send_reset_email(user):
    print(f"User ID: {user.id}")           
    print(f"User Email: {user.email}")     
    print(f"User Name: {user.username}")
    print(f"random: {os.environ.get('EMAIL_USER')}")
    token = user.get_reset_token()
    msg = Message('Password Reset Request', sender = 'noreply@demo.com', recipients = [user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token = token, _external = True)}

If you did not make this request then simply this email and no changes will be made.
'''
    mail.send(msg)

@app.route("/reset_password", methods = ['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        send_reset_email(user)
        flash("A request code has been sent to your email.", "info")
        return redirect(url_for('login'))
    return render_template('reset_request.html', title = 'Reset Password', form = form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)