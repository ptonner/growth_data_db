from ..operation import PlateOperation
import logging

class PlateDelete(PlateOperation):

    def _run(self):
        if not self.plate is None:
            if not self.plate.data_table is None:
                if self.plate.data_table in self.core.metadata.tables.keys():
                    table = self.core.metadata.tables[self.plate.data_table]
                    table.drop(self.core.engine)
                    self.core.metadata.remove(table)
                else:
                    logging.error("plate %s data_table not in metadata"%self.plateName)
            else:
                logging.error("plate %s data_table is None"%self.plateName)
            self.core.session.delete(self.plate)
        else:
            logging.error("plate %s missing"%self.plateName)
