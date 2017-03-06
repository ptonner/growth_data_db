from hypothesis import given, settings
import hypothesis.strategies as st

import popmachine
from utils import platename, StatelessDatabaseTest
from dataset.fullfactorial import fullfactorialDataset
from dataset import incomplete

class TestPlate(StatelessDatabaseTest):


    @given(platename, fullfactorialDataset)
    def test_plate_creation_and_deletion_fullfactorial(self, name , dataset):
        self.general_plate_create_test( name, dataset)

    @given(platename, incomplete.dataset())
    def test_plate_creation_and_deletion_incomplete(self, name , dataset):
        self.general_plate_create_test( name, dataset)

    def general_plate_create_test(self, name, dataset):

        assert not name in self.machine.plates(names=True)

        plate = self.machine.createPlate(name,data=dataset.data,experimentalDesign=dataset.meta)

        assert not plate is None
        assert name in self.machine.plates(names=True)
        assert plate in self.machine.plates(names=False)
        assert not plate.data_table is None
        data_table = plate.data_table
        assert data_table in self.machine.metadata.tables

        self.machine.deletePlate(name)

        assert not name in self.machine.plates(names=True)
        assert not plate in self.machine.plates(names=False)
        assert not data_table in self.machine.metadata.tables
