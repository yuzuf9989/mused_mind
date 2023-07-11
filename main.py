from flask import Flask, render_template, redirect, url_for, request, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from functools import wraps
from forms import CreatePostForm, CommentBox, RegisterUser, LoginUser


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
login_manager = LoginManager()
login_manager.login_view = 'login'
ckeditor = CKEditor(app)
Bootstrap(app)
login_manager.init_app(app)

# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
error = None


# CONFIGURE TABLES
class Users(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    blogs = relationship('BlogPost', back_populates='user')
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('users.id'), nullable=False)
    user = relationship("Users", back_populates="blogs")
    author = db.Column(db.String(250), nullable=False)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)


# with app.app_context():
#     db.create_all()

def admin_only(function):
    wraps(function)

    def decorated_func(*args, **kwargs):
        if current_user.id != 1:
            return abort(code=403)
        return function(*args, **kwargs)
    decorated_func.__name__ = function.__name__
    return decorated_func


@login_manager.user_loader
def load_user(user_id):
    with app.app_context():
        user = db.session.query(Users).filter_by(id=user_id).first()
        return user


@app.route('/', methods=["POST", "GET"])
def get_all_posts():
    posts = db.session.query(BlogPost).all()
    return render_template("index.html", all_posts=posts)


@app.route('/register', methods=["POST", "GET"])
def register():
    global error
    error = request.args.get('error')
    form = RegisterUser()
    if request.method == "POST":
        name = request.form.get('Name')
        email = request.form.get('Email')
        password = request.form.get('Password')
        hash_password = generate_password_hash(password=password, method='pbkdf2', salt_length=16)
        if db.session.query(Users).filter_by(email=email).first():
            error = 'Email already in use! Please log in... '
            return redirect(url_for('login', error=error))
        else:
            new_user = Users()
            new_user.name = name
            new_user.email = email
            new_user.password = hash_password
            with app.app_context():
                db.session.add(new_user)
                db.session.commit()
                user = db.session.query(Users).filter_by(email=email).first()
                login_user(user)
            logged_in = True
            return redirect(url_for('get_all_posts', logged_in=logged_in))
    return render_template("register.html", form=form, error=error)


@app.route('/login', methods=["POST", "GET"])
def login():
    global error
    error = request.args.get('error')
    form = LoginUser()
    if request.method == "POST":
        email = request.form.get('Email')
        password = request.form.get('Password')
        user = db.session.query(Users).filter_by(email=email).first()
        if user:
            check_pass = user.password
            if check_password_hash(check_pass, password):
                login_user(user)
                return redirect(url_for('get_all_posts'))
            else:
                error = 'Bad Credentials! Please Try Again...'
        else:
            error = 'No such user found! Please Register...'
            return redirect(url_for('register', error=error))
    return render_template("login.html", form=form, error=error)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>")
def show_post(post_id):
    requested_post = db.session.query(BlogPost).filter_by(id=post_id).first()
    comment_form = CommentBox()
    return render_template("post.html", post=requested_post, form=comment_form)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/new-post", methods=["POST", "GET"])
@login_required
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            user_id=current_user.id,
            title=request.form.get('Post Title'),
            subtitle=request.form.get('Subtitle'),
            body=request.form.get('Content'),
            img_url=request.form.get('Image URL'),
            author=current_user.name,
            date=date.today().strftime("%B %d, %Y"),
        )
        with app.app_context():
            db.session.add(new_post)
            db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>", methods=["POST", "GET"])
@login_required
@admin_only
def edit_post(post_id):
    old_post = db.session.query(BlogPost).filter_by(id=post_id).first()
    edit_form = CreatePostForm(
        title=old_post.title,
        subtitle=old_post.subtitle,
        img_url=old_post.img_url,
        body=old_post.body
    )
    if edit_form.validate_on_submit():
        with app.app_context():
            new_post = db.session.query(BlogPost).filter_by(id=post_id).first()
            new_post.title = request.form.get('Post Title')
            new_post.subtitle = request.form.get('Subtitle')
            new_post.img_url = request.form.get('Image URL')
            new_post.body = request.form.get('Content')
            db.session.commit()
        return redirect(url_for("show_post", post_id=old_post.id))
    return render_template("make-post.html", form=edit_form)


@app.route("/delete/<int:post_id>")
@login_required
@admin_only
def delete_post(post_id):
    with app.app_context():
        post_to_delete = db.session.query(BlogPost).filter_by(id=post_id).first()
        db.session.delete(post_to_delete)
        db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(debug=True)
