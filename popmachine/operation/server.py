from operation import Operation
import popmachine
from popmachine.application.app import create_app


class ServerOperation(Operation):

    argsKwargs = [('url', 'db_url')]

    def __init__(self, core, url, **kwargs):
        Operation.__init__(self, core)
        self.url = url

    def _run(self):

        app = create_app()

        # app.machine = self.core
        app.run(debug=False, host='0.0.0.0')
