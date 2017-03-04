import popmachine, itertools, unittest
from hypothesis import given, settings
import hypothesis.strategies as st
import pandas as pd
from utils import fullfactorialDataset, platename, StatelessDatabaseTest

import sys

# class TestPlate(unittest.TestCase):
class TestPlate(StatelessDatabaseTest):

    # @given(platename.filter(lambda x: not x in machine.plates(names=True)), fullfactorialDataset)
    @given(platename, fullfactorialDataset)
    # @settings(max_examples=30)
    def test_plate_creation_and_deletion(self, name , dataset):

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
