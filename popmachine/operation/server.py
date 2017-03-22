from operation import Operation
from popmachine.application.app import app

class ServerOperation(Operation):

    def _run(self):
        app.run()
