from core import Core
from models import Plate, Design, Well, ExperimentalDesign, well_experimental_design
from dataset import DataSet
from sqlalchemy.sql import select, false
from sqlalchemy import Column, Float
import pandas as pd
from plate import create, delete
import search.query

class Machine(Core):

    def __init__(self, database='.popmachine.db'):
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

    def get(self, wells, include=[]):
        """Given a query on wells, return a dataset with the wells's data."""

        if wells.count()==0:
            return None

        designs = self.session.query(Design)
        if len(include) > 0:
            designs = designs.filter(Design.name.in_(include))
        else:
            designs = designs.filter(false())

        metacols = [d.name for d in designs]

        meta = data = None

        plates = self.session.query(Plate).join(Well)
        plates = plates.filter(Well.id.in_([w.id for w in wells]))

        for p in plates:
            subwells = wells.filter(Well.plate==p)
            cols = [Column('time', Float)]+[Column(str(w.plate_number), Float) for w in subwells]

            table = self.metadata.tables[p.data_table]
            s = select(cols,from_obj=table)
            res = self.engine.execute(s)

            newdata = pd.DataFrame(list(res), columns = ['time'] + ["%d_%d"%(p.id,w.plate_number) for w in subwells])
            if data is None:
                data = newdata
            else:
                data = pd.merge(data,newdata,on='time')

            newmeta = []
            for w in subwells:
                newmeta.append([p.name, w.plate_number])
                for c in metacols:
                    design = self.session.query(Design).filter(Design.name==c).one()
                    ed = self.session.query(ExperimentalDesign).filter(\
                                                 ExperimentalDesign.design==design,\
                                                 ExperimentalDesign.wells.contains(w)).one()
                    newmeta[-1].append(ed.get_value())

            newmeta = pd.DataFrame(newmeta, columns = ['plate', 'number']+metacols)
            if meta is None:
                meta = newmeta
            else:
                meta = pd.concat((meta, newmeta))

        data.index = data.time
        del data['time']
        data = data.astype(float)

        for i in include:
            if not i in meta.columns:
                logging.warning('no design %s found, ignored' % i)

        return DataSet(data, meta)

    def filter(self, plates=[], numbers=[], *args, **kwargs):
        wells = self.session.query(Well)
        wells = wells.join(well_experimental_design)#.join(ExperimentalDesign)

        # if plates provided, filter on those
        if isinstance(plates, list) and len(plates)>0:
            wells = wells.join(Plate)
            wells = wells.filter(Plate.name.in_(plates))
        elif isinstance(plates, str) or isinstance(plates, unicode):
            wells = wells.join(Plate)
            wells = wells.filter(Plate.name==plates)
            plates = [plates]

        # if numbers are provided, filter those
        if isinstance(numbers, list) and len(numbers)>0:
            wells = wells.filter(Well.plate_number.in_(numbers))

        wells = search.query.query(wells, **kwargs)

        return wells

    def search(self, plates=[], numbers=[], include=[], *args, **kwargs):
        q = self.filter(plates, numbers, **kwargs)
        return self.get(q, include+kwargs.keys())
