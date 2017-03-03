import popmachine, utils
from hypothesis import given, settings
import hypothesis.strategies as st
import unittest
import numpy as np
from utils import machine, platename, fullfactorialDataset

class TestSearch(unittest.TestCase):

    @given(utils.platename, utils.fullfactorialDataset)
    @settings(max_examples=10)
    def test_search_returns_same_data(self,name,dataset):
        utils.machine.createPlate(name,data=dataset.data,experimentalDesign=dataset.meta)

        search = machine.search(plates=[name], include=dataset.meta.columns)

        del search.meta['plate']

        assert search == dataset, search

    @given(platename, platename.filter(lambda x: not x in machine.plates(names=True)), fullfactorialDataset)
    @settings(max_examples=10)
    def test_search_ignores_garbage_plate_names(self,name, other,dataset):
        utils.machine.createPlate(name,data=dataset.data,experimentalDesign=dataset.meta)

        search = machine.search(plates=[name, other], include=dataset.meta.columns)

        del search.meta['plate']

        assert search == dataset, search

    @given(utils.platename.filter(lambda x: not x in machine.plates(names=True)), utils.fullfactorialDataset)
    @settings(max_examples=10)
    def test_search_individual_samples(self, name, ds):

        utils.machine.createPlate(name,data=ds.data,experimentalDesign=ds.meta)

        for i, r in ds.meta.iterrows():
            search = machine.search(plates=[name], **r)
            del search.meta['plate']

            assert ds.data.iloc[:,i].equals(search.data[0])

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
