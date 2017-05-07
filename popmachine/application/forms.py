from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, FileField, SelectField, PasswordField, IntegerField
from wtforms.validators import DataRequired, Email
# from validators import DataValidator


class RegisterForm(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    name = StringField('name', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    password_confirm = PasswordField('password', validators=[DataRequired()])
    email = StringField('email', validators=[DataRequired(), Email()])


class LoginForm(FlaskForm):
    name = StringField('user name', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default=False)


class SearchForm(FlaskForm):
    search = StringField("search")


class PhenotypeForm(FlaskForm):
    name = StringField('name')


class PlateCreate(FlaskForm):
    name = StringField('name')
    # data = FileField('data',validators=[DataValidator()])
    data = FileField('data')
    design = FileField('design')
    ignore = StringField('ignore')
    source = SelectField("source", choices=[
                         ('csv', 'csv'), ('bioscreen', 'bioscreen')])


class ProjectForm(FlaskForm):

    name = StringField('name')
    description = StringField('description')
    design = StringField('design')
    published = BooleanField('published')

    citation = StringField('citation')
    citation_pmid = IntegerField('citation_pmid')


class DesignForm(FlaskForm):
    type = SelectField("type", choices=[
                       ('str', 'str'), ('int', 'int'), ('float', 'float'), ('bool', 'bool')])
