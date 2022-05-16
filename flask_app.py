from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_ckeditor import CKEditor
from forms import *
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_bootstrap import Bootstrap
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask_gravatar import Gravatar



app = Flask(__name__)

app.config['SECRET_KEY'] = '123456789'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


ckeditor = CKEditor(app)

Bootstrap(app)

# Create a login manager
login_manager = LoginManager()
login_manager.init_app(app)

gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


db = SQLAlchemy(app)
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(250), nullable=False)
    admin_status = db.Column(db.Boolean, nullable=False)

class BlogPost(db.Model):
    __tablename__ = "blogposts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    author = relationship("User", backref="blogs")
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))


    def get_col_names():
        """Returns the column names of the blogpost table object"""
        return [column.name for column in BlogPost.__table__.columns]

    def to_dict(self):
        """Returns the data in a particular table as a dictionary """
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}

class Comments(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(250), nullable=False)
    owner = relationship("User", backref="comments")
    on_blog = relationship("BlogPost", backref="comments")
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    on_blog_id = db.Column(db.Integer, db.ForeignKey("blogposts.id"))

db.create_all()

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated and current_user.admin_status:
            return f(*args, **kwargs)
        else:
            return abort(403)
    return decorated_function

def super_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated and current_user.id == 1:
            return f(*args, **kwargs)
        else:
            return abort(403)
    return decorated_function


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/make-admin', methods=["GET", "POST"])
@super_admin
def make_admin():
    all_users = User.query.all()
    admins = dynamic_form(all_users)
    form = admins(request.form)
    for field in form:
        user_id = int(field.id)
        this_user = User.query.get(user_id)

        if this_user.admin_status:
            field.checked = True
    if request.method == 'POST':
        for key, value in form.data.items():
            user = User.query.get(int(key))
            user.admin_status = value
            db.session.commit()
        return redirect(url_for('index'))

    return render_template('admin.html', users=all_users, form=form)


@app.route('/delete-post/<int:index>', methods=["POST"])
@admin_only
def delete_post(index):
    try:
        post_to_delete = BlogPost.query.get(index)
        db.session.delete(post_to_delete)
        db.session.commit()
    finally:
        return redirect(url_for('index'))


@app.route('/add-post', methods=["POST", "GET"])
@admin_only
def add_post():
    made_posts = [blog.title for blog in BlogPost.query.all()]
    form = AddBlogForm(made_posts)
    if form.validate_on_submit():
        today = datetime.date.today().strftime('%B %d,%Y')
        valid_inputs = {key: value for (key, value) in form.data.items() if key in BlogPost.get_col_names()}
        new_blog = BlogPost(**valid_inputs, date=today, author=current_user)
        db.session.add(new_blog)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_new_post.html', form=form)


@app.route('/edit-post/<int:index>', methods=["POST", "GET"])
@admin_only
def edit_post(index):
    requested_post = BlogPost.query.get(index)
    other_posts = [blog.title for blog in BlogPost.query.all() if blog.title != requested_post.title]
    edit_form = AddBlogForm(other_posts)

    if request.method == 'GET':
        edit_form.process(**requested_post.to_dict())

    if edit_form.validate_on_submit():
        requested_post.title = edit_form.title.data
        requested_post.subtitle = edit_form.subtitle.data
        requested_post.body = edit_form.body.data
        requested_post.img_url = edit_form.img_url.data
        db.session.commit()
        return redirect(url_for('post', index=requested_post.id))
    return render_template('add_new_post.html', form=edit_form, edit=requested_post)


@app.route('/delete-comment/<int:comment_id>', methods=["GET"])
@login_required
def delete_comment(comment_id):
    comment_delete = Comments.query.get(comment_id)
    post_id = comment_delete.on_blog.id
    db.session.delete(comment_delete)
    db.session.commit()
    return redirect(url_for('post', index=post_id))


@app.route('/post/<int:index>', methods=["POST", "GET"])
def post(index):
    requested_post = BlogPost.query.get(index)
    form = CommentForm()
    if form.validate_on_submit():
        new_comment = Comments(content=form.body.data, owner=current_user, on_blog=requested_post)
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('post', index=requested_post.id))
    return render_template('post.html', post=requested_post, form=form)


@app.route('/register', methods=["POST", "GET"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():

        present = User.query.filter_by(email=form.email.data).first()
        if present:
            flash("You're already registered. Just log in", 'success')
            return redirect(url_for("login"))

        pw_hash = generate_password_hash(form.password.data, salt_length=8)
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=pw_hash,
            admin_status=False
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('index'))
    return render_template('register.html', form=form)


@app.route("/login", methods=["POST", "GET"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        present = User.query.filter_by(email=form.email.data).first()
        if not present:
            flash("You haven't registered yet", 'danger ')
            return redirect(url_for("login"))

        if check_password_hash(present.password, form.password.data):
            login_user(present)
            return redirect(url_for('index'))
    return render_template('login.html', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/')
def index():
    all_blogs = BlogPost.query.all()
    return render_template('index.html', posts=all_blogs)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)