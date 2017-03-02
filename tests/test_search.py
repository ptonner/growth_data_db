import popmachine, utils
from hypothesis import given
import hypothesis.strategies as st
import unittest

machine = popmachine.Machine('.test.db')

class TestSearch(unittest.TestCase):

    @given(utils.buildDataset())
    def test_search_returns_same_data(self,dataset):
        data, meta = dataset

        num = len(list(machine.list(popmachine.models.Plate)))
        machine.createPlate('test%d'%num,data=data,experimentalDesign=meta)

        ds = machine.search(plates=['test%d'])
        
        data.index = data[0]
        del data[0]

        assert (abs(ds.data-data)<1e-9).all()
