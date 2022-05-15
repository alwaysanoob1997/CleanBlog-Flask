from flask import Flask, render_template, redirect, url_for
from flask_ckeditor import CKEditor
from forms import *
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_bootstrap import Bootstrap
import datetime




app = Flask(__name__)

app.config['SECRET_KEY'] = '123456789'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


ckeditor = CKEditor(app)

Bootstrap(app)


db = SQLAlchemy(app)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(250), nullable=False)

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    author = db.Column(db.String(250), nullable=False)
    # author_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    # author = relationship("User", backref="blogs")

    def get_col_names():
        """Returns the column names of the blogpost table object"""
        return [column.name for column in BlogPost.__table__.columns]

class Comments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(250), nullable=False)
    # owner = relationship("User", backref="comments")
    # on_blog = relationship("BlogPost", backref="comments")
    # owner_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    # on_blog_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))

db.create_all()


@app.route('/add-post', methods=["POST", "GET"])
def add_post():
    made_posts = [blog.title for blog in BlogPost.query.all()]
    form = AddBlogForm(made_posts)
    if form.validate_on_submit():
        today = datetime.date.today().strftime('%B %d,%Y')
        valid_inputs = {key: value for (key, value) in form.data.items() if key in BlogPost.get_col_names()}
        new_blog = BlogPost(**valid_inputs, date=today)
        db.session.add(new_blog)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_new_post.html', form=form)


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

@app.route('/post/<int:index>')
def post(index):
    requested_post = BlogPost.query.get(index)
    return render_template('post.html', post=requested_post)


if __name__ == '__main__':
    app.run(debug=True)