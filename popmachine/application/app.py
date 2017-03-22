from flask import Flask

app = Flask('popmachine.application')
app.config.from_object('popmachine.application.config')

from . import views
