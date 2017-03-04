from utils import fullfactorialDataset
from hypothesis import given, settings
from popmachine import DataSet

@given(fullfactorialDataset)
def test_dataset_equality(ds):

    ds2 = DataSet(ds.data, ds.meta)

    assert ds == ds2
    assert ds2 == ds

    assert ds != 1
    assert ds != 1.0
    assert ds != 'fdsafdsa'

@given(fullfactorialDataset)
def test_dataset_copy(ds):

    ds2 = ds.copy()

    assert ds == ds2
    assert ds2 == ds
