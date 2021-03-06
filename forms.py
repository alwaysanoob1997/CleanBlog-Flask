from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Email, URL, NoneOf
from flask_ckeditor import CKEditorField
from wtforms import StringField, SubmitField, URLField, EmailField, PasswordField, BooleanField, FieldList, SelectField, Form, TextAreaField
import email_validator
from flask import request
import bleach


## strips invalid tags/attributes
def strip_invalid_html(content):
    allowed_tags = ['a', 'abbr', 'acronym', 'address', 'b', 'br', 'div', 'dl', 'dt',
                    'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img',
                    'li', 'ol', 'p', 'pre', 'q', 's', 'small', 'strike',
                    'span', 'sub', 'sup', 'table', 'tbody', 'td', 'tfoot', 'th',
                    'thead', 'tr', 'tt', 'u', 'ul', 'blockquote', 'cite', 'strong']

    allowed_attrs = {
        'a': ['href', 'target', 'title'],
        'img': ['src', 'alt', 'width', 'height']
    }

    cleaned = bleach.clean(content,
                           tags=allowed_tags,
                           attributes=allowed_attrs,
                           strip=True)

    return cleaned


def AddBlogForm(titles:list):
    present_titles = titles
    class BlogAdd(FlaskForm):
        title = StringField("Title:", validators=[DataRequired(), NoneOf(present_titles, message="Sorry,you've got to get another title, this one's already taken")])
        subtitle = StringField("Subtitle:", validators=[DataRequired()])
        img_url = URLField("URL for blog image:", validators=[DataRequired(), URL(message="Not a valid URL")])
        body = CKEditorField("Body:", validators=[DataRequired()])
        submit = SubmitField("Submit")

    return BlogAdd()


class RegisterForm(FlaskForm):
    name = StringField("Name:", validators=[DataRequired()])
    email = EmailField("Email:", validators=[DataRequired(), Email()])
    password = PasswordField("Password:", validators=[DataRequired()])
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    email = EmailField("Email:", validators=[DataRequired(), Email()])
    password = PasswordField("Password:", validators=[DataRequired()])
    submit = SubmitField("Log In")


class CommentForm(FlaskForm):
    body = TextAreaField("", validators=[DataRequired()])
    submit = SubmitField("COMMENT")

def dynamic_form(list_a):
    class Admin(Form):
        pass

    for user in list_a:
        setattr(Admin, f"{user.id}", BooleanField(user.name, default="checked"))

    return Admin