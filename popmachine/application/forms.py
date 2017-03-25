from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, FileField, SelectField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    openid = StringField('openid', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default=False)

class SearchForm(FlaskForm):
    search = StringField("search")

class PlateCreate(FlaskForm):
    name = StringField('name')
    data = FileField('data')
    design = FileField('design')
    ignore = StringField('ignore')
    source = SelectField("source", choices=[('csv', 'csv'), ('bioscreen', 'bioscreen')])

class DesignForm(FlaskForm):
    type = SelectField("type", choices=[('str', 'str'), ('int', 'int'), ('float', 'float'), ('bool', 'bool')])
