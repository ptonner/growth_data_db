from hypothesis import given, settings, find
import hypothesis.strategies as st
import pandas as pd
import numpy as np

import popmachine
from ..utils import platename, StatelessDatabaseTest, charstring
from ..dataset.incomplete import designSpace, dataset, sharedDesignSpace, compendia

def checkSearchForPlates(search, name, dataset):
    """check that search contains the right values for the provided datasets"""

    assert dataset.meta.shape[0] == (search.meta.plate==name).sum()

    # compare returned data to replicates matching the design in the original data
    if dataset.meta.shape[0] > 0:
        select = search.meta.plate==name
        temp = popmachine.DataSet(search.data.loc[:,select], search.meta.loc[select,:])
        temp.data.columns = temp.meta.number
        del temp.meta['plate']
        del temp.meta['number']

        # select = (dataset.meta[columns] == values).all(1)
        # temp2 = popmachine.DataSet(d.data.loc[:,select], d.meta.loc[select,:])

        assert all(temp.data.columns == dataset.data.columns)

        merge = pd.merge(temp.data, dataset.data,\
                            left_index=True, right_index=True,\
                            how='inner')
        diff = merge.iloc[:,:merge.shape[1]/2].values - merge.iloc[:,merge.shape[1]/2:].values

        assert (np.isnan(diff) | np.isclose(diff, 0)).all(), diff

class TestSearch(StatelessDatabaseTest):

    @given(platename, dataset())
    def test_search_returns_same_data(self,name,dataset):
        self.machine.createPlate(name,data=dataset.data,experimentalDesign=dataset.meta)

        search = self.machine.search(plates=[name], include=dataset.meta.columns)

        del search.meta['plate']; del search.meta['number']

        assert search == dataset, search

        self.machine.deletePlate(name)

    @given(platename, platename, dataset())
    def test_search_ignores_garbage_plate_names(self,name, other,dataset):

        plate = self.machine.createPlate(name,data=dataset.data,experimentalDesign=dataset.meta)

        search = self.machine.search(plates=[name, other], include=dataset.meta.columns)

        del search.meta['plate']; del search.meta['number']

        assert search == dataset, search.data

        self.machine.deletePlate(name)

    @given(platename,dataset())
    def test_search_individual_samples(self, name, ds):

        plate = self.machine.createPlate(name,data=ds.data,experimentalDesign=ds.meta)

        assert not plate is None

        for i, r in ds.meta.iterrows():
            search = self.machine.search(plates=[name], numbers=[i], **r)
            del search.meta['plate']; del search.meta['number']

            assert ds.data.iloc[:,i].equals(search.data[0])

        self.machine.deletePlate(name)

    @given(st.lists(platename,min_size=2,max_size=2, unique=True),dataset())
    def test_search_matching_design_single_plate(self, names, ds):

        n1, n2 = names
        assert not n1 in self.machine.plates(names=True)
        assert not n2 in self.machine.plates(names=True)

        p1 = self.machine.createPlate(names[0],data=ds.data,experimentalDesign=ds.meta)
        p2 = self.machine.createPlate(names[1],data=ds.data,experimentalDesign=ds.meta)

        search = self.machine.search(plates=[names[0]],include=ds.meta.columns.tolist())
        del search.meta['plate']; del search.meta['number']
        assert search == ds

        search = self.machine.search(plates=[names[1]],include=ds.meta.columns.tolist())
        del search.meta['plate']; del search.meta['number']
        assert search == ds

        for c in ds.meta.columns:
            search = self.machine.search(plates=[names[0]], **{c:ds.meta[c].unique().tolist()})
            assert not names[1] in search.meta['plate'].tolist()

        self.machine.deletePlate(names[0])
        self.machine.deletePlate(names[1])

    @given(platename, dataset(),st.lists(charstring, min_size=1))
    def test_search_individual_samples_with_garbage_include(self, name, ds, other):

        self.machine.createPlate(name,data=ds.data,experimentalDesign=ds.meta)

        for i, r in ds.meta.iterrows():
            search = self.machine.search(plates=[name], include=other, numbers=[i], **r)
            del search.meta['plate']; del search.meta['number']

            assert ds.data.iloc[:,i].equals(search.data[0])

        self.machine.deletePlate(name)

    @given(sharedDesignSpace, compendia())
    def test_compendia_search(self, dsp, cmp):
        """Test that a compendia of datasets from a shared designspace can be searched properly."""

        names, datasets = cmp

        plates = []
        for ds, n in zip(datasets, names):
            plates.append(self.machine.createPlate(n,ds.data,ds.meta))

        # search each design
        for i, r in dsp.iterrows():

            # determine how many replicates across all datasets have this design
            count = 0
            for d in datasets:
                count += (d.meta == r).all(1).sum()

            search = self.machine.search(**r)

            # check search results match compendia and dataset properties and values
            if count == 0:
                assert search is None
            else:
                assert search.data.shape[1] == count
                for n,d in zip(names,datasets):

                    select = (d.meta == r).all(1)
                    temp2 = popmachine.DataSet(d.data.loc[:,select], d.meta.loc[select,:])
                    checkSearchForPlates(search, n, temp2)
