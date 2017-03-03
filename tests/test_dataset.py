from utils import machine, fullfactorialDataset
from hypothesis import given, settings
from popmachine import DataSet

@given(fullfactorialDataset)
def test_dataset_equality(ds):

    ds2 = DataSet(ds.data, ds.meta)

    assert ds == ds2
    assert ds2 == ds
