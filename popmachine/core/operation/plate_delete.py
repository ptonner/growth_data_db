from operation import PlateOperation
from ...models import Plate, Well, Design, ExperimentalDesign

class PlateDelete(PlateOperation):

    def _run(self):
        if not self.plate is None:
            if not self.plate.data_table is None:
                self.core.metadata.tables[self.plate.data_table].drop(self.core.engine)
            self.core.session.delete(self.plate)
