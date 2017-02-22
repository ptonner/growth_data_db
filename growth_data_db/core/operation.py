import logging
from ..models import  Project, Plate, Well, Design, ExperimentalDesign

class Operation(object):
    """General operation object of the system."""

    def __init__(self, core):
        self.core = core

    def run(self):
        self._run()

    def _run(self):
        raise NotImplemented()

class ProjectOperation(Operation):
    """Any operation specifying a project."""

    def __init__(self,core,project,createIfMissing=False):
        Operation.__init__(self,core)

        self.projectName = project

        self.project = self.core.session.query(Project).filter(Project.name==project).one_or_none()
        if self.project is None:
            if createIfMissing:
                logging.warning("creating new project %s"%args.project)
                self.project = Project(name=args.project,plates=[])
                self.core.session.add(project)
            else:
                raise ValueError("no project named %s!"%project)

class PlateOperation(ProjectOperation):
    """Any operation specifying a plate (and by necessity its project)."""

    def __init__(self, core, project, plate,createIfMissing=False):
        ProjectOperation.__init__(self,core, project,createIfMissing)

        self.plateName = plate

        self.plate = self.core.session.query(Plate).filter(Plate.name==plate, Plate.project==self.project).one_or_none()
