from core import Core
from models import Project, Plate, Design, Well, ExperimentalDesign, well_experimental_design
from dataset import DataSet
from sqlalchemy.sql import select, false, or_
from sqlalchemy import Column, Float
import pandas as pd
from plate import create, delete
import search

class Machine(Core):

    def __init__(self, database='sqlite:///.popmachine.db'):
        Core.__init__(self, database)

    def list(self, table):

        if not table in [Plate, Design, Well]:
            raise ValueError()

        q = self.session.query(table)
        for r in q:
            yield r

    def plates(self,names=False):
        plates = self.list(Plate)
        if names:
            return [p.name for p in plates]
        return plates

    def designs(self,names=False):
        designs = self.list(Design)
        if names:
            return [p.name for p in designs]
        return designs

    def wells(self):
        return self.list(Well)

    def createPlate(self, *args, **kwargs):
        po = create.PlateCreate(self, *args, **kwargs)
        ret = po.run()
        self.session.commit()
        return ret

    def deletePlate(self, plate, *args, **kwargs):
        pd = delete.PlateDelete(self, plate, *args, **kwargs)
        ret = pd.run()
        self.session.commit()

        return ret

    def get(self,*args, **kwargs):
        return search.get.get(self.session, self.metadata, self.engine, *args, **kwargs)

    def _get_intermediate(self, q, include=[], *args, **kwargs):

        return search.get.get(self.session, self.metadata, self.engine, q, include=include+kwargs.keys())

    def filter(self, projects=[], plates=[], numbers=[], *args, **kwargs):
    # def filter(self, plates=[], numbers=[], *args, **kwargs):
        wells = self.session.query(Well)
        wells = wells.join(well_experimental_design)#.join(ExperimentalDesign)

        # if projects provided, filter on those
        if isinstance(projects, list) and len(projects)>0:
            wells = wells.join(Plate).join(Project)
            wells = wells.filter(or_(Project.name.in_(projects), Project.nickname.in_(projects)))
        elif isinstance(projects, str) or isinstance(projects, unicode):
            wells = wells.join(Plate).join(Project)
            wells = wells.filter(or_(Project.name==projects, Project.nickname==projects))

        # if plates provided, filter on those
        if isinstance(plates, list) and len(plates)>0:
            wells = wells.join(Plate)
            wells = wells.filter(Plate.name.in_(plates))
        elif isinstance(plates, str) or isinstance(plates, unicode):
            wells = wells.join(Plate)
            wells = wells.filter(Plate.name==plates)

        # if numbers are provided, filter those
        if isinstance(numbers, list) and len(numbers)>0:
            wells = wells.filter(Well.plate_number.in_(numbers))

        wells = search.query.query(wells, self, **kwargs)

        return wells

    def search(self, projects=[], plates=[], numbers=[], include=[], *args, **kwargs):
        q = self.filter(projects, plates, numbers, **kwargs)

        return search.get.get(self.session, self.metadata, self.engine, q, include=include+kwargs.keys())
        # return self.get(q, include+kwargs.keys())
