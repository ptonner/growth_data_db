from core import Core
from models import Plate, Design, Well, ExperimentalDesign
from dataset import DataSet
from sqlalchemy.sql import select
import pandas as pd

class Machine(object):

    def __init__(self, database='.popmachine.db'):

        self.core = Core(database)

    def list(self, table):

        if not table in [Plate, Design]:
            raise ValueError()

        q = self.core.session.query(table)
        for r in q:
            yield r

    def search(self,include=[], *args, **kwargs):
        """search the database for wells matching the provided kwargs

        For each key, value pair filter wells with matching experimental designs. If the value of the pair is a list, any possible value in the list is accepted."""


        wells = self.core.session.query(Well)

        metacols = []

        for k,v in kwargs.iteritems():
            design = self.core.session.query(Design).filter(Design.name==k).one_or_none()

            if design is None:
                continue
            metacols.append(k)

            experimentalDesigns = self.core.session.query(ExperimentalDesign).filter(\
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

        for i in include:
            design = self.core.session.query(Design).filter(Design.name==i).one_or_none()

            if design is None:
                continue
            metacols.append(i)

        plates = self.core.session.query(Plate).filter(Plate.id.in_(set([w.plate.id for w in wells])))

        data = None
        meta = None

        for p in plates:
            subwells = wells.filter(Well.plate==p)
            cols = ['time']+[str(w.plate_number) for w in subwells]

            table = self.core.metadata.tables[p.data_table]
            s = select(cols,from_obj=table)
            res = self.core.engine.execute(s)

            newdata = pd.DataFrame(list(res), columns = ['time'] + ["%d_%d"%(p.id,w.plate_number) for w in subwells])
            if data is None:
                data = newdata
            else:
                data = pd.merge(data,newdata,on='time')

            newmeta = []
            for w in subwells:
                newmeta.append([])
                for c in metacols:
                    design = self.core.session.query(Design).filter(Design.name==c).one()
                    ed = self.core.session.query(ExperimentalDesign).filter(\
                                                 ExperimentalDesign.design==design,\
                                                 ExperimentalDesign.wells.contains(w)).one()
                    newmeta[-1].append(ed.get_value())

            newmeta = pd.DataFrame(newmeta, columns = metacols)
            if meta is None:
                meta = newmeta
            else:
                meta = pd.concat((meta, newmeta))

        data.index = data.time
        del data['time']

        return DataSet(data, meta)
