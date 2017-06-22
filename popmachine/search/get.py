from ..models import Plate, Design, Well, ExperimentalDesign
from sqlalchemy import Column, Float
from sqlalchemy.sql import select, false
from ..dataset import DataSet
import pandas as pd
import logging

def get(session, metadata, engine, wells, include=[]):
    """Given a query on wells, return a dataset with the wells's data."""

    if wells.count()==0:
        return None

    designs = session.query(Design)
    if len(include) > 0:
        designs = designs.filter(Design.name.in_(include))
    else:
        designs = designs.filter(false())

    metacols = [d.name for d in designs]

    meta = data = None

    plates = session.query(Plate).join(Well)
    plates = plates.filter(Well.id.in_([w.id for w in wells]))

    for p in plates:
        subwells = wells.filter(Well.plate==p)
        cols = [Column('time', Float)]+[Column(str(w.plate_number), Float) for w in subwells]

        table = metadata.tables[p.data_table]
        s = select(cols,from_obj=table)
        res = engine.execute(s)

        newdata = pd.DataFrame(list(res), columns = ['time'] + ["%d_%d"%(p.id,w.plate_number) for w in subwells])
        if data is None:
            data = newdata
        else:
            data = pd.merge(data,newdata,on='time', how='outer')

        newmeta = []
        for w in subwells:
            newmeta.append([p.name, w.plate_number])
            for c in metacols:
                design = session.query(Design).filter(Design.name==c).one()
                ed = session.query(ExperimentalDesign).filter(\
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
