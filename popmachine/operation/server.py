from operation import Operation
from popmachine.application.app import app

class ServerOperation(Operation):

    def _run(self):
        app.run(debug=False,host='0.0.0.0')
