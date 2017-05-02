from flask import Flask


app = Flask('popmachine.application')
app.config.from_object('popmachine.application.config')
app.secret_key = 'some_secret'

from . import views
views.login_manager.init_app(app)
