from flask import Flask
from flask_mail import Mail
import blueprints

app = Flask('popmachine.application')
app.config.from_object('popmachine.application.config')
app.secret_key = 'some_secret'
app.register_blueprint(blueprints.project.profile)
app.register_blueprint(blueprints.plate.profile)
app.register_blueprint(blueprints.design.profile)
app.register_blueprint(blueprints.model.profile)

mail = Mail(app)

from . import views
views.login_manager.init_app(app)
