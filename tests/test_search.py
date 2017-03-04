import popmachine, utils
from hypothesis import given, settings, find
import hypothesis.strategies as st
import unittest
import numpy as np
from utils import machine, platename, fullfactorialDataset

class TestSearch(utils.StatelessDatabaseTest):

    @given(utils.platename, utils.fullfactorialDataset)
    @settings(max_examples=5)
    def test_search_returns_same_data(self,name,dataset):
        utils.machine.createPlate(name,data=dataset.data,experimentalDesign=dataset.meta)

        search = machine.search(plates=[name], include=dataset.meta.columns)

        del search.meta['plate']

        assert search == dataset, search

        machine.deletePlate(name)

    @given(platename, platename, fullfactorialDataset)
    @settings(max_examples=5)
    def test_search_ignores_garbage_plate_names(self,name, other,dataset):

        plate = utils.machine.createPlate(name,data=dataset.data,experimentalDesign=dataset.meta)

        search = machine.search(plates=[name, other], include=dataset.meta.columns)

        del search.meta['plate']

        assert search == dataset, search

        machine.deletePlate(name)

    @given(utils.platename,utils.fullfactorialDataset)
    @settings(max_examples=5)
    def test_search_individual_samples(self, name, ds):

        plate = utils.machine.createPlate(name,data=ds.data,experimentalDesign=ds.meta)

        assert not plate is None

        for i, r in ds.meta.iterrows():
            search = machine.search(plates=[name], **r)
            del search.meta['plate']

            assert ds.data.iloc[:,i].equals(search.data[0])

        machine.deletePlate(name)

    @given(st.lists(utils.platename,min_size=2,max_size=2, unique=True),\
            utils.fullfactorialDataset)
    @settings(max_examples=5)
    def test_search_matching_design_single_plate(self, names, ds):

        p1 = utils.machine.createPlate(names[0],data=ds.data,experimentalDesign=ds.meta)
        p2 = utils.machine.createPlate(names[1],data=ds.data,experimentalDesign=ds.meta)

        for c in ds.meta.columns:
            search = utils.machine.search(plates=names[0], c=ds.meta[c].unique())
            assert not names[1] in search.meta['plate']

        machine.deletePlate(names[0])
        machine.deletePlate(names[1])

    @given(utils.platename, utils.fullfactorialDataset,\
            st.lists(utils.charstring.filter(lambda x: not x in machine.designs(names=True)), min_size=1))
    @settings(max_examples=5)
    def test_search_individual_samples_with_garbage_include(self, name, ds, other):

        utils.machine.createPlate(name,data=ds.data,experimentalDesign=ds.meta)

        for i, r in ds.meta.iterrows():
            search = machine.search(plates=[name], include=other, **r)
            del search.meta['plate']

            assert ds.data.iloc[:,i].equals(search.data[0])

        machine.deletePlate(name)
