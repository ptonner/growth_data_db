from operation import Operation

import logging, os
import pandas as pd

class Import(Operation):

    argsKwargs = Operation.argsKwargs + [('project',None), ('directory', None), ('data', None), ('experimentalDesign', None),]

    def __init__(self,core, project, directory, data='data.csv', experimentalDesign='meta.csv',**kwargs):
        Operation.__init__(self, core)

        self.project = project

        while directory[-1] == '/':
            directory = directory[:-1]
        self.directory = directory

        _,self.name = os.path.split(self.directory)

        self.datafile = data
        self.metafile = experimentalDesign

    def _run(self):

        self.data = pd.read_csv(os.path.join(self.directory,self.datafile))
        self.meta = pd.read_csv(os.path.join(self.directory,self.metafile))

        self.core.createPlate(self.project, self.name, data=self.data, experimentalDesign=self.meta)
