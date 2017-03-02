import popmachine, itertools
from hypothesis import given
import hypothesis.strategies as st
import pandas as pd
import unittest

# utility for making character string with limited range
charstring = st.characters(min_codepoint=1, max_codepoint=100, blacklist_categories=('Cc', 'Cs'))

@st.composite
def buildMeta(draw, maxFactors, maxTreatments):
    numDesigns = draw(st.lists(st.integers(min_value=1, max_size=maxTreatments), min_size=1, max_size=maxFactors))
    designs = [draw(st.lists(st.text(charstring,min_size=1), min_size=d, max_size=d)) for d in numDesigns]
    names = draw(st.lists(charstring, min_size=len(designs), max_size=len(designs)))

    meta = [list(x) for x in itertools.product(*designs)]
    meta = pd.DataFrame(meta, columns = names)

    return meta

@st.composite
def buildDataset(draw, minDesigns=1, maxDesigns=3, maxTreatments=3):

    numDesigns = draw(st.lists(st.integers(min_value=1, max_value=maxTreatments), min_size=1, max_size=maxDesigns))
    designs = [draw(st.lists(st.text(st.characters(min_codepoint=1, max_codepoint=100, blacklist_categories=('Cc', 'Cs')),min_size=1), min_size=d, max_size=d)) for d in numDesigns]
    names = draw(st.lists(charstring, min_size=len(designs), max_size=len(designs)))

    meta = [list(x) for x in itertools.product(*designs)]

    l = len(meta[0])
    p = len(meta)

    data = [draw(st.lists(st.floats(), min_size=p+1, max_size=p+1)) for i in range(l)]
    # meta = [draw(st.lists(st.floats(), min_size=l, max_size=l)) for i in range(p+1)]

    data = pd.DataFrame(data)
    meta = pd.DataFrame(meta, columns = names)

    return popmachine.DataSet(data, meta)
