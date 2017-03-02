import popmachine, itertools
from hypothesis import given, settings
import hypothesis.strategies as st
import pandas as pd
from utils import buildDataset

machine = popmachine.Machine('.test.db')

# utility for making character string with limited range
charstring = st.characters(min_codepoint=1, max_codepoint=100, blacklist_categories=('Cc', 'Cs'))

# @st.composite
# def buildMeta(draw, numDesigns=None, maxFactors=10, maxTreatments=100):
#
#     if numDesigns is None:
#         numDesigns = draw(st.lists(st.integers(min_value=1, max_size=maxTreatments), min_size=1, max_size=maxFactors))
#
#     designs = [draw(st.lists(st.text(charstring,min_size=1), min_size=d, max_size=d)) for d in numDesigns]
#
#     meta = [list(x) for x in itertools.product(*designs)]
#     return meta

# @given(buildDataset())
# def test_build_data_shape(dataset):
#     assert dataset.data.shape[1] == dataset.meta.shape[0]

@given(buildDataset())
@settings(max_examples=10)
def test_creating_plate(dataset):
    num = len(list(machine.list(popmachine.models.Plate)))

    machine.createPlate('test%d'%num,data=dataset.data,experimentalDesign=dataset.meta)
