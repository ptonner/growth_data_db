from hypothesis import given
import hypothesis.strategies as st
from dataset.incomplete import designSpace, dataset

sharedDesignSpace = st.shared(designSpace(), key='dsp')

# @given(designSpace(), dataset())
@given(sharedDesignSpace, dataset(sharedDesignSpace))
def test_incomplete_dataset_comes_from_designspace(dsp, ds):

    for i in range(ds.meta.shape[0]):
        assert (ds.meta.iloc[i,:] == dsp).all(1).any()
