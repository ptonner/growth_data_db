from operation import PlateOperation
from ..models import Plate, Well
from .. import api
import logging
import pandas as pd

class PlateCreate(PlateOperation):

    def __init__(self,core, project, plate, data, experimentalDesign, timeColumn=0, createIfMissing=False):
        PlateOperation.__init__(self, core, project, plate, createIfMissing)
        self.dataFile = data
        self.experimentalDesignFile = experimentalDesign
        self.timeColumn = timeColumn

    def _run(self):

        if not self.plate is None:
            logging.error("plate named %s already exists in project %s!"%(self.plate, self.project))
            return

        self.plate = Plate(name=self.plateName,project=self.project)
        self.core.session.add(self.plate)
        self.core.session.commit()

        self.data = pd.read_csv(self.dataFile)
        self.meta = pd.read_csv(self.experimentalDesignFile)

        data_columns = range(self.data.shape[1])
        data_columns.remove(self.timeColumn)

        wells = [Well(plate=self.plate,plate_number=n) for n in data_columns]
        self.core.session.add_all(wells)
        self.core.session.commit()

        table = api.upload.create_plate_data_table(self.plate,self.core)
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
                api.add_experimental_design(self.core,c,u,*temp)
