import popmachine, utils
from hypothesis import given, settings
import hypothesis.strategies as st
import unittest
import numpy as np
from utils import machine

class TestSearch(unittest.TestCase):

    @given(utils.platename, utils.fullfactorialDataset)
    @settings(max_examples=5)
    def test_search_returns_same_data(self,name,dataset):

        num = len(list(machine.list(popmachine.models.Plate)))
        utils.machine.createPlate(name,data=dataset.data,experimentalDesign=dataset.meta)

        search = machine.search(plates=[name])

        del search.meta['plate']

        # assert search == dataset, search

        nan_or_zero = lambda x: np.isnan(x) or abs(x) < 1e-9
        assert ((search.data-dataset.data).applymap(nan_or_zero)).all().all(), search.data-dataset.data

    # @given(utils.fullfactorialDataset, utils.fullfactorialDataset, utils.fullfactorialDataset)
    # @settings(max_examples=5)
    # def test_search_three_plates(self,ds1, ds2, ds3):
    #
    #     plates = []
    #     for ds in [ds1, ds2, ds3]:
    #         num = len(list(machine.list(popmachine.models.Plate)))
    #
    #         machine.createPlate('test%d'%num,data=ds.data,experimentalDesign=ds.meta)
    #         plates.append('test%d'%num)
    #
    #
    #     search = machine.search(plates=plates, )
