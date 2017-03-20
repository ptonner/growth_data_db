from hypothesis import given
import hypothesis.strategies as st
import itertools
import pandas as pd
import popmachine
from operator import mul
from ..utils import charstring

@st.composite
def fullfactorialData(draw, minDesigns=1, maxDesigns=3, maxTreatments=3):
    numDesigns = draw(st.shared(st.lists(st.integers(min_value=1, max_value=maxTreatments), min_size=minDesigns, max_size=maxDesigns), key='numDesigns'))

    # total number of replicates
    p = reduce(mul, numDesigns, 1)

    # number of observations
    n = draw(st.integers(min_value=1, max_value=100))

    time = draw(st.lists(st.floats(allow_infinity=False, allow_nan=False), min_size=n, max_size=n, unique=True))
    data = draw(st.lists(st.lists(st.floats(), min_size=p, max_size=p), min_size=n, max_size=n))

    return [[t]+d for t,d in zip(time, data)]

    # return draw(st.lists(st.lists(st.floats(), min_size=p+1, max_size=p+1), min_size=n, max_size=n))

@st.composite
def fullfactorialMeta(draw, minDesigns=1, maxDesigns=3, maxTreatments=3):
    # numDesigns = draw(st.lists(st.integers(min_value=1, max_size=maxTreatments), min_size=1, max_size=maxFactors))
    numDesigns = draw(st.shared(st.lists(st.integers(min_value=1, max_value=maxTreatments), min_size=minDesigns, max_size=maxDesigns), key='numDesigns'))

    designs = [draw(st.lists(st.text(charstring,min_size=1), min_size=d, max_size=d, unique=True)) for d in numDesigns]
    names = draw(st.lists(charstring, min_size=len(designs), max_size=len(designs), unique=True))

    meta = [list(x) for x in itertools.product(*designs)]
    meta = pd.DataFrame(meta, columns = names)

    return meta


fullfactorialDataset = st.builds(popmachine.DataSet,
                            fullfactorialData(), fullfactorialMeta())
