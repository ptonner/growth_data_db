from operation import Operation
from ...models import Design

class DesignList(Operation):
    """List designs in the database"""

    # argsKwargs = [('project', None)]

    def __init__(self,core):
        Operation.__init__(self,core)

        self.designs = self.core.session.query(Design).all()

    def _run(self):

        for d in self.designs:
            print d
