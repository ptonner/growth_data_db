from flask import Flask
from flask_mail import Mail

app = Flask('popmachine.application')
app.config.from_object('popmachine.application.config')
app.secret_key = 'some_secret'

mail = Mail(app)

from . import views
views.login_manager.init_app(app)
