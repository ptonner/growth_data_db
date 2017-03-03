import popmachine, itertools
from hypothesis import given
import hypothesis.strategies as st
import pandas as pd
import unittest
from operator import mul
import numpy as np

# stop telling me about comparing NaN's!!!
np.seterr(invalid='ignore')

machine = popmachine.Machine('.test.db')

# utility for making character string with limited range
simplechars = st.characters(min_codepoint=1, max_codepoint=100, blacklist_categories=('Cc', 'Cs'))
charstring = st.text(simplechars, min_size=1)

# platename = st.text(simplechars, min_size=5).filter(lambda x: not x in [p.name for p in machine.list(popmachine.models.Plate)])
platename = st.text(simplechars, min_size=5)

@st.composite
def fullfactorialData(draw, minDesigns=1, maxDesigns=3, maxTreatments=3):
    numDesigns = draw(st.shared(st.lists(st.integers(min_value=1, max_value=maxTreatments), min_size=minDesigns, max_size=maxDesigns), key='numDesigns'))

    # total number of replicates
    p = reduce(mul, numDesigns, 1)

    # number of observations
    n = draw(st.integers(min_value=1, max_value=100))

    return draw(st.lists(st.lists(st.floats(), min_size=p+1, max_size=p+1), min_size=n, max_size=n))

@st.composite
def fullfactorialMeta(draw, minDesigns=1, maxDesigns=3, maxTreatments=3):
    # numDesigns = draw(st.lists(st.integers(min_value=1, max_size=maxTreatments), min_size=1, max_size=maxFactors))
    numDesigns = draw(st.shared(st.lists(st.integers(min_value=1, max_value=maxTreatments), min_size=minDesigns, max_size=maxDesigns), key='numDesigns'))

    designs = [draw(st.lists(st.text(charstring,min_size=1), min_size=d, max_size=d)) for d in numDesigns]
    names = draw(st.lists(charstring, min_size=len(designs), max_size=len(designs), unique=True))

    meta = [list(x) for x in itertools.product(*designs)]
    meta = pd.DataFrame(meta, columns = names)

    return meta

# @st.composite
# def buildDatasetComponents(draw, minDesigns=1, maxDesigns=3, maxTreatments=3):
#
#     numDesigns = draw(st.lists(st.integers(min_value=1, max_value=maxTreatments), min_size=1, max_size=maxDesigns))
#     designs = [draw(st.lists(st.text(st.characters(min_codepoint=1, max_codepoint=100, blacklist_categories=('Cc', 'Cs')),min_size=1), min_size=d, max_size=d)) for d in numDesigns]
#     names = draw(st.lists(charstring, min_size=len(designs), max_size=len(designs)))
#
#     meta = [list(x) for x in itertools.product(*designs)]
#
#     l = len(meta[0])
#     p = len(meta)
#
#     data = [draw(st.lists(st.floats(), min_size=p+1, max_size=p+1)) for i in range(l)]
#     # meta = [draw(st.lists(st.floats(), min_size=l, max_size=l)) for i in range(p+1)]
#
#     data = pd.DataFrame(data)
#     meta = pd.DataFrame(meta, columns = names)
#
#     return data, meta

fullfactorialDataset = st.builds(popmachine.DataSet,
                            fullfactorialData(), fullfactorialMeta())
