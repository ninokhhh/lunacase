from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Email, Length

class RegisterForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(min=2)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Register")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class ProductForm(FlaskForm):
    title = StringField("Product title", validators=[DataRequired()])
    price = IntegerField("Price", validators=[DataRequired()])
    img = StringField("Image URL", validators=[DataRequired()])
    submit = SubmitField("Add product")