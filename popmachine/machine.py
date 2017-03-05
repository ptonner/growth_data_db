from core import Core
from models import Plate, Design, Well, ExperimentalDesign
from dataset import DataSet
from sqlalchemy.sql import select
from sqlalchemy import Column, Float
import pandas as pd
from plate import create, delete

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

    def search(self, plates=[],include=[], *args, **kwargs):
        """search the database for wells matching the provided kwargs

        arguments:
        For each key, value pair filter wells with matching experimental designs. If the value of the pair is a list, any possible value in the list is accepted."""


        wells = self.session.query(Well)

        # if plates provided, filter on those
        if isinstance(plates, list) and len(plates)>0:
            wells = wells.join(Plate)
            wells = wells.filter(Plate.name.in_(plates))
        elif isinstance(plates, str):
            wells = wells.join(Plate)
            wells = wells.filter(Plate.name==plates)

        metacols = []

        for k,v in kwargs.iteritems():
            design = self.session.query(Design).filter(Design.name==k).one_or_none()

            if design is None:
                continue
            metacols.append(k)

            experimentalDesigns = self.session.query(ExperimentalDesign).filter(\
                                            ExperimentalDesign.design==design)

            if isinstance(v, list):
                # convert non-string values
                v = [str(z) for z in v]

                experimentalDesigns = experimentalDesigns.filter(\
                                                ExperimentalDesign.value.in_(v))
            else:
                # convert non-string values
                v = str(v)

                experimentalDesigns = experimentalDesigns.filter(\
                                                ExperimentalDesign.value==v)


            filterwells = []
            for ed in experimentalDesigns.all():
                filterwells.extend([w.id for w in ed.wells if not w in filterwells and not w is None])

            wells = wells.filter(Well.id.in_(filterwells))

        if wells.count()==0:
            return None

        # don't duplicate columns we're already using
        include = filter(lambda x : not x in metacols, include)

        for i in include:
            design = self.session.query(Design).filter(Design.name==i).one_or_none()

            if design is None or design.name in metacols:
                continue
            metacols.append(i)

        # plates = self.session.query(Plate).filter(Plate.id.in_(set([w.plate.id for w in wells])))
        plates = self.session.query(Plate).join(Well)
        plates = plates.filter(Well.id.in_([w.id for w in wells]))

        data = None
        meta = None

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
                newmeta.append([p.name])
                for c in metacols:
                    design = self.session.query(Design).filter(Design.name==c).one()
                    ed = self.session.query(ExperimentalDesign).filter(\
                                                 ExperimentalDesign.design==design,\
                                                 ExperimentalDesign.wells.contains(w)).one()
                    newmeta[-1].append(ed.get_value())

            newmeta = pd.DataFrame(newmeta, columns = ['plate']+metacols)
            if meta is None:
                meta = newmeta
            else:
                meta = pd.concat((meta, newmeta))

        data.index = data.time
        del data['time']
        data = data.astype(float)

        return DataSet(data, meta)
