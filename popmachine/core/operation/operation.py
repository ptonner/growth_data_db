import logging
from ...models import Plate, Well, Design, ExperimentalDesign

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
        self._run()

    def _run(self):
        raise NotImplemented()

# class ProjectOperation(Operation):
#     """Any operation specifying a project."""
#
#     argsKwargs = [('project', None)]
#
#     def __init__(self,core,project,createIfMissing=False):
#         Operation.__init__(self,core)
#
#         self.projectName = project
#
#         self.project = self.core.session.query(Project).filter(Project.name==project).one_or_none()
#         if self.project is None:
#             if createIfMissing:
#                 logging.warning("creating new project %s"%project)
#                 self.project = Project(name=project,plates=[])
#                 self.core.session.add(self.project)
#             else:
#                 raise ValueError("no project named %s!"%project)

class PlateOperation(Operation):
    """Any operation specifying a plate (and by necessity its project)."""

    argsKwargs = [('plate', None)]

    def __init__(self, core, plate, createIfMissing=False):
        Operation.__init__(self, core)

        self.plateName = plate
        self.plate = self.core.session.query(Plate).filter(Plate.name==plate).one_or_none()
