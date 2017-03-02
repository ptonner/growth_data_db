import popmachine, utils
from hypothesis import given, settings
import hypothesis.strategies as st
import unittest
import numpy as np

machine = popmachine.Machine('.test.db')

class TestSearch(unittest.TestCase):

    @given(utils.fullfactorialDataset)
    @settings(max_examples=5)
    def test_search_returns_same_data(self,dataset):

        num = len(list(machine.list(popmachine.models.Plate)))
        machine.createPlate('test%d'%num,data=dataset.data,experimentalDesign=dataset.meta)

        ds = machine.search(plates=['test%d'%num])

        nan_or_zero = lambda x: np.isnan(x) or abs(x) < 1e-9
        assert ((ds.data-dataset.data).applymap(nan_or_zero)).all().all(), ds.data-dataset.data

    # @given(utils.fullfactorialDataset())
    # @settings(max_examples=5)
    # def test_search_design(self,dataset):
    #
    #     num = len(list(machine.list(popmachine.models.Plate)))
    #
    #     machine.createPlate('test%d'%num,data=dataset.data,experimentalDesign=dataset.meta)
    #
    #     for i in range(dataset.meta.shape[0]):
    #         kw = dataset.meta.iloc[i,:]
    #         print kw
    #         # search = machine.search(plates=['test%d'%num], **kw)
    #
    #         # assert (abs(ds.data-dataset.data)<1e-9).all().all(), ds.data-dataset.data
