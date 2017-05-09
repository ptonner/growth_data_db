from operation import Operation
import popmachine
from popmachine.application.app import app

class ServerOperation(Operation):

    argsKwargs = [('url', 'db-url')]

    def _run(self, url):

        app.machine = popmachine.Machine(url)
        app.run(debug=False,host='0.0.0.0')
