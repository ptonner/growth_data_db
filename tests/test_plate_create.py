from hypothesis import given, settings
import hypothesis.strategies as st

import popmachine
from utils import platename, StatelessDatabaseTest
from dataset.fullfactorial import fullfactorialDataset
from dataset import incomplete

def plate_create_check(machine, name, dataset):

    assert not name in machine.plates(names=True)

    plate = machine.createPlate(name,data=dataset.data,experimentalDesign=dataset.meta)

    assert not plate is None
    assert name in machine.plates(names=True)
    assert plate in machine.plates(names=False)
    assert not plate.data_table is None
    data_table = plate.data_table
    assert data_table in machine.metadata.tables

    machine.deletePlate(name)

    assert not name in machine.plates(names=True)
    assert not plate in machine.plates(names=False)
    assert not data_table in machine.metadata.tables

class TestPlate(StatelessDatabaseTest):

    @given(platename, fullfactorialDataset)
    def test_plate_creation_and_deletion_fullfactorial(self, name , dataset):
        plate_create_check(self.machine, name, dataset)

    @given(platename, incomplete.dataset())
    def test_plate_creation_and_deletion_incomplete(self, name , dataset):
        plate_create_check(self.machine, name, dataset)
