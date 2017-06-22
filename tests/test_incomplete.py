from hypothesis import given, settings, HealthCheck
import hypothesis.strategies as st
from dataset.incomplete import dataset, sharedDesignSpace

def assert_dataset_in_designspace(ds, dsp):
    for i in range(ds.meta.shape[0]):
        assert (ds.meta.iloc[i,:] == dsp).all(1).any()
        assert (ds.meta.iloc[i,:] == dsp).all(1).sum() == 1

@given(sharedDesignSpace, dataset(sharedDesignSpace))
def test_incomplete_dataset_comes_from_designspace(dsp, ds):
    assert_dataset_in_designspace(ds, dsp)

@given(sharedDesignSpace, st.lists(dataset(sharedDesignSpace), min_size=1,max_size=5))
@settings(suppress_health_check=[HealthCheck.data_too_large])
def test_incomplete_compedia_comes_from_designspace(dsp, datasets):
    for ds in datasets:
        assert_dataset_in_designspace(ds, dsp)
