import logging
from ..models import Project, Plate

def query_or_copy(core, obj, model):

    """If obj's type is model, return obj and its name. Otherwise return the
        query of model with name matching obj."""

    if isinstance(obj, str) or isinstance(obj, unicode):
        name = obj
        obj = core.session.query(model).filter(model.name==name).one_or_none()
    elif isinstance(obj, model):
        name = obj.name
    else:
        raise ValueError()

    return obj, name

class Operation(object):
    """General operation object of the system."""

    # list of (k1, k2) value pairs mapping args object value names (k2) to class
    # constructor key word values (k1). None for k2 implies ==k1
    argsKwargs = []

    @classmethod
    def fromArgs(cls, core, args, **kwargs):
        """Method for creating operation from command line args"""

        kw = {}
        for k1,k2 in cls.argsKwargs:
            if k2 is None:
                k2 = k1

            if k2 in vars(args):
                kw[k1] = vars(args)[k2]

        kw.update(kwargs)

        return cls(core, **kw)

    def __init__(self, core):
        self.core = core

    def run(self):
        return self._run()

    def _run(self):
        raise NotImplemented()

class PlateOperation(Operation):
    """Any operation specifying a plate."""

    argsKwargs = [('project', None), ('plate', None)]

    def __init__(self, core, project, plate, *args, **kwargs):
        Operation.__init__(self, core)

        self.project, self.projectName = query_or_copy(self.core, project, Project)

        if isinstance(plate, str) or isinstance(plate, unicode):
            self.plateName = plate
            self.plate = self.core.session.query(Plate).filter(Plate.name==plate).one_or_none()
        elif isinstance(plate, Plate):
            self.plate = plate
            self.plateName = self.plate.name
        else:
            raise ValueError()
