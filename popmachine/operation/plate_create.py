from operation import PlateOperation
from ..models import Plate, Well, Design, ExperimentalDesign

from sqlalchemy import Table, Column, Integer, String, Interval, MetaData, ForeignKey, Float, or_, and_
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

import logging
import pandas as pd

def create_plate_data_table(plate, core):
    """create a data_table for the provided plate, doing nothing if it already exists."""

    if not plate.data_table is None:
        return core.metadata.tables[plate.data_table]

    well_numbers = [w.plate_number for w in plate.wells]

    cols = [Column('id', Integer, primary_key=True), Column('time', Float)] + \
        [Column(str(wn), Float) for wn in well_numbers]

    table = Table(u'_plate_data_%d'%plate.id,core.metadata,*cols)
    core.metadata.create_all(core.engine)

    plate.data_table = table.name
    core.session.add(plate)
    core.session.commit()

    return table

# def copy_plate_dataframe_to_table(data,table,data_columns,column_names):
#
# 	conn = engine.connect()
# 	ins = table.insert()
#
# 	# add each row to the table
# 	for i in range(data.shape[0]):
# 		newrow = dict([('time',data.iloc[i,0])] + [(cn,data.iloc[i,j]) for cn,j in zip(column_names,data_columns)])
# 		conn.execute(ins,**newrow)

def add_experimental_design(core,design_name,design_value,*args,**kwargs):
    # check if design exists, create if needed
    design = core.session.query(Design).filter(Design.name==design_name).one_or_none()
    if not design:
        if not 'design_type' in kwargs:
            logging.info("design %s does not exist, and no design_type is specified to create a new one. using str as default"%design_name)
            design_type='str'
        else:
            design_type = kwargs['design_type']

        design = Design(name=design_name,type=design_type)
        core.session.add(design)

    experimentalDesign = core.session.query(ExperimentalDesign).filter(ExperimentalDesign.design==design,ExperimentalDesign.value==design_value).one_or_none()

    if experimentalDesign is None:
        logging.info("ExperimentalDesign %s=%s does not exist, creating one"%(design_name, design_value))
        experimentalDesign = ExperimentalDesign(design=design, value=design_value)

    # for each well
    # check if design value exists, create if needed
    for well in args:
        if isinstance(well,Well):
            # dv = models.ExperimentalDesign(design=design,well=well,value=design_value)
            well.experimentalDesigns.append(experimentalDesign)
            # core.session.add(dv)

    core.session.commit()

class PlateCreate(PlateOperation):

    argsKwargs = PlateOperation.argsKwargs + [('data', None), ('experimentalDesign', None), ('timeColumn', None)]

    def __init__(self,core, plate, data, experimentalDesign, timeColumn=0, createIfMissing=False, **kwargs):
        PlateOperation.__init__(self, core, plate, createIfMissing)
        self.dataFile = data
        self.experimentalDesignFile = experimentalDesign
        self.timeColumn = timeColumn

        self.extraDesigns = kwargs

    def _run(self):

        if not self.plate is None:
            logging.error("plate named %s already exists!"%(self.plate))
            return

        self.plate = Plate(name=self.plateName)
        self.core.session.add(self.plate)
        self.core.session.commit()

        self.data = pd.read_csv(self.dataFile)
        self.meta = pd.read_csv(self.experimentalDesignFile)

        data_columns = range(self.data.shape[1])
        data_columns.remove(self.timeColumn)

        wells = [Well(plate=self.plate,plate_number=n) for n in data_columns]
        self.core.session.add_all(wells)
        self.core.session.commit()

        table = create_plate_data_table(self.plate,self.core)
        self.core.session.commit()

        # copy in data
        conn = self.core.engine.connect()
        ins = table.insert()

        # add each row to the table
        for i in range(self.data.shape[0]):
            newrow = dict([('time',self.data.iloc[i,0])] + [(str(j),self.data.iloc[i,j]) for j in data_columns])
            conn.execute(ins,**newrow)

        # add experimental designs
        for c in self.meta.columns:
            for u in self.meta[c].unique():
                select = self.meta[c] == u
                temp = [w for w,s in zip(wells, select.tolist()) if s]
                add_experimental_design(self.core,c,u,*temp)

        # add extra designs
        for k,v in self.extraDesigns.iteritems():
            add_experimental_design(self.core,k,v,*wells)
