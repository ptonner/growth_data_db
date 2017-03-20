from flask import Flask

app = Flask(__name__)
app.config.from_object('popmachine.application.config')

from . import views
