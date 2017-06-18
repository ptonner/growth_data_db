from flask import Flask
from flask_mail import Mail
from flask_login import LoginManager
from popmachine import Machine


from itsdangerous import URLSafeTimedSerializer


class PopmachineFlask(Flask):

    def setup_db(self):
        self.machine = Machine(self.config['DATABASE'])
        self.ts = URLSafeTimedSerializer(self.config["SECRET_KEY"])

# app = PopmachineFlask('popmachine.application', instance_relative_config=True)
# app.config.from_pyfile('config.py')
#
# machine = Machine(app.config['DATABASE'])


mail = Mail()
login_manager = LoginManager()

# from . import views
# views.login_manager.init_app(app)

import blueprints


def create_app():

    app = PopmachineFlask('popmachine.application',
                          instance_relative_config=True)
    app.config.from_pyfile('config.py')
    app.setup_db()

    mail.init_app(app)
    login_manager.init_app(app)

    app.register_blueprint(blueprints.misc.profile)
    app.register_blueprint(blueprints.project.profile)
    app.register_blueprint(blueprints.plate.profile)
    app.register_blueprint(blueprints.design.profile)
    app.register_blueprint(blueprints.model.profile)
    app.register_blueprint(blueprints.account.profile)

    return app
