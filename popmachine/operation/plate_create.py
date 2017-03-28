from operation import PlateOperation

import logging
import pandas as pd

class PlateCreate(PlateOperation):

    argsKwargs = PlateOperation.argsKwargs + [('data', None), ('experimentalDesign', None), ('timeColumn', None), ('directory', None)]

    def __init__(self,core, plate, data, experimentalDesign, timeColumn=0, createIfMissing=False, directory="", **kwargs):
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

        self.core.createPlate(plate, data=self.data, experimentalDesign = self.experimentalDesign)
