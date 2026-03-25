from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, URL, NumberRange


class RegisterForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Create Account")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class ProductForm(FlaskForm):
    product_url = StringField("Product URL", validators=[DataRequired(), URL(), Length(max=1000)])
    title = StringField("Title Override", validators=[Optional(), Length(max=500)])
    target_price = FloatField("Target Price", validators=[Optional(), NumberRange(min=0)])
    is_tracking_enabled = BooleanField("Enable Tracking", default=True)
    submit = SubmitField("Track Product")


class ProductEditForm(FlaskForm):
    title = StringField("Product Title", validators=[DataRequired(), Length(max=500)])
    target_price = FloatField("Target Price", validators=[Optional(), NumberRange(min=0)])
    is_tracking_enabled = BooleanField("Enable Tracking")
    submit = SubmitField("Update Product")
