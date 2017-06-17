from flask import Flask
from flask_mail import Mail
from popmachine import Machine

app = Flask('popmachine.application', instance_relative_config=True)
app.config.from_object('popmachine.application.config')
app.config.from_pyfile('config.py')

machine = Machine(app.config['DATABASE'])

import blueprints
app.register_blueprint(blueprints.project.profile)
app.register_blueprint(blueprints.plate.profile)
app.register_blueprint(blueprints.design.profile)
app.register_blueprint(blueprints.model.profile)


mail = Mail(app)

from . import views
views.login_manager.init_app(app)
