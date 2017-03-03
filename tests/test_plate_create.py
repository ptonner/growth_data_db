import popmachine, itertools
from hypothesis import given, settings
import hypothesis.strategies as st
import pandas as pd
from utils import fullfactorialDataset, platename, machine

@given(platename, fullfactorialDataset)
@settings(max_examples=10)
def test_creating_plate(name,dataset):
    num = len(list(machine.list(popmachine.models.Plate)))

    machine.createPlate(name,data=dataset.data,experimentalDesign=dataset.meta)
