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
            print d, [v.get_value() for v in d.values]


class DesignSetType(Operation):

    argsKwargs = [('design',None), ('type', None)]

    def __init__(self,core,design,type):
        Operation.__init__(self,core)

        self.type = type

        self.design = self.core.session.query(Design).filter(Design.name==design).one_or_none()

        if self.design is None:
            raise ValueError("No design named %s"%design)

    def _run(self):

        self.design.type = self.type
        self.core.session.add(self.design)
