from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL, Length
from flask_ckeditor import CKEditorField

# WTForm
class CreatePostForm(FlaskForm):
    title = StringField(name="Post Title", validators=[DataRequired()])
    subtitle = StringField(name="Subtitle", validators=[DataRequired()])
    img_url = StringField(name="Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField(name="Content", validators=[DataRequired()])
    submit = SubmitField(name="Submit Post")


class RegisterUser(FlaskForm):
    name = StringField(name='Name', validators=[DataRequired()])
    email = StringField(name='Email', validators=[DataRequired()])
    password = PasswordField(name='Password', validators=[DataRequired()])
    submit = SubmitField(name='Join in')


class LoginUser(FlaskForm):
    email = StringField(name='Email', validators=[DataRequired()])
    password = PasswordField(name='Password', validators=[DataRequired()])
    submit = SubmitField(name='Let me in')


class CommentBox(FlaskForm):
    comments = CKEditorField(name="Comments", validators=[DataRequired(), Length(min=3, max=100)])
    submit = SubmitField(name="Post Comment")