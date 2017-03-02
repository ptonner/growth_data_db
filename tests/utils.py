import popmachine, itertools
from hypothesis import given
import hypothesis.strategies as st
import pandas as pd
import unittest

# utility for making character string with limited range
charstring = st.characters(min_codepoint=1, max_codepoint=100, blacklist_categories=('Cc', 'Cs'))

@st.composite
def buildMeta(draw, numDesigns=None, maxFactors=10, maxTreatments=100):

    if numDesigns is None:
        numDesigns = draw(st.lists(st.integers(min_value=1, max_size=maxTreatments), min_size=1, max_size=maxFactors))

    designs = [draw(st.lists(st.text(charstring,min_size=1), min_size=d, max_size=d)) for d in numDesigns]

    meta = [list(x) for x in itertools.product(*designs)]
    return meta

@st.composite
def buildDataset(draw, maxFactors=3, maxTreatments=10):
    # p = draw(st.integers(min_value=1, max_value=100))
    # l = draw(st.integers(min_value=1, max_value=100))

    numDesigns = draw(st.lists(st.integers(min_value=1, max_value=maxFactors), min_size=1, max_size=maxTreatments))
    designs = [draw(st.lists(st.text(st.characters(min_codepoint=1, max_codepoint=100, blacklist_categories=('Cc', 'Cs')),min_size=1), min_size=d, max_size=d)) for d in numDesigns]

    meta = [list(x) for x in itertools.product(*designs)]

    l = len(meta[0])
    p = len(meta)

    data = [draw(st.lists(st.floats(), min_size=p+1, max_size=p+1)) for i in range(l)]
    # meta = [draw(st.lists(st.floats(), min_size=l, max_size=l)) for i in range(p+1)]

    data = pd.DataFrame(data)
    meta = pd.DataFrame(meta)

    return data, meta
