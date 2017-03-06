from hypothesis import given, settings, find
import hypothesis.strategies as st

import popmachine
from ..utils import platename, StatelessDatabaseTest, charstring
from ..dataset.incomplete import designSpace, dataset, sharedDesignSpace

class TestSearch(StatelessDatabaseTest):

    @given(platename, dataset())
    def test_search_returns_same_data(self,name,dataset):
        self.machine.createPlate(name,data=dataset.data,experimentalDesign=dataset.meta)

        search = self.machine.search(plates=[name], include=dataset.meta.columns)

        del search.meta['plate']

        assert search == dataset, search

        self.machine.deletePlate(name)

    @given(platename, platename, dataset())
    def test_search_ignores_garbage_plate_names(self,name, other,dataset):

        plate = self.machine.createPlate(name,data=dataset.data,experimentalDesign=dataset.meta)

        search = self.machine.search(plates=[name, other], include=dataset.meta.columns)

        del search.meta['plate']

        assert search == dataset, search.data

        self.machine.deletePlate(name)

    @given(platename,dataset())
    def test_search_individual_samples(self, name, ds):

        plate = self.machine.createPlate(name,data=ds.data,experimentalDesign=ds.meta)

        assert not plate is None

        for i, r in ds.meta.iterrows():
            search = self.machine.search(plates=[name], numbers=[i], **r)
            del search.meta['plate']

            assert ds.data.iloc[:,i].equals(search.data[0])

        self.machine.deletePlate(name)

    @given(st.lists(platename,min_size=2,max_size=2, unique=True),dataset())
    def test_search_matching_design_single_plate(self, names, ds):

        n1, n2 = names
        assert not n1 in self.machine.plates(names=True)
        assert not n2 in self.machine.plates(names=True)

        p1 = self.machine.createPlate(names[0],data=ds.data,experimentalDesign=ds.meta)
        p2 = self.machine.createPlate(names[1],data=ds.data,experimentalDesign=ds.meta)

        search = self.machine.search(plates=names[0],include=ds.meta.columns.tolist())
        del search.meta['plate']
        assert search == ds

        search = self.machine.search(plates=names[1],include=ds.meta.columns.tolist())
        del search.meta['plate']
        assert search == ds

        for c in ds.meta.columns:
            search = self.machine.search(plates=names[0], **{c:ds.meta[c].unique().tolist()})
            assert not names[1] in search.meta['plate']

        self.machine.deletePlate(names[0])
        self.machine.deletePlate(names[1])

    @given(platename, dataset(),st.lists(charstring, min_size=1))
    def test_search_individual_samples_with_garbage_include(self, name, ds, other):

        self.machine.createPlate(name,data=ds.data,experimentalDesign=ds.meta)

        for i, r in ds.meta.iterrows():
            search = self.machine.search(plates=[name], include=other, **r)
            del search.meta['plate']

            assert ds.data.iloc[:,i].equals(search.data[0])

        self.machine.deletePlate(name)
