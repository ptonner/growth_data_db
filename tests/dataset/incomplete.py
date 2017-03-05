from hypothesis import given
import hypothesis.strategies as st

import popmachine, itertools
import pandas as pd
from ..utils import charstring

@st.composite
def designSpace(draw, minDesigns=1, maxDesigns=3, maxTreatments=3):

    minDesigns = max(minDesigns, 1)
    maxDesigns = max(minDesigns, maxDesigns)
    maxTreatments = max(maxTreatments, 1)

    designSize = st.integers(min_value=1, max_value=maxTreatments)
    designSizes = draw(st.lists(designSize, min_size=minDesigns, max_size=maxDesigns))

    designs = [draw(st.lists(st.text(charstring,min_size=1), min_size=d, max_size=d, unique=True)) for d in designSizes]
    names = draw(st.lists(charstring, min_size=len(designs), max_size=len(designs), unique=True))

    designspace = [list(x) for x in itertools.product(*designs)]
    designspace = pd.DataFrame(designspace, columns = names)

    return designspace

@st.composite
def dataset(draw, designspace=designSpace(),nrep=st.integers(min_value=0, max_value=3),\
            nobs=st.integers(min_value=0,max_value=100), observations=st.floats(),\
            time=st.floats(allow_infinity=False, allow_nan=False)):

    dsp = draw(designspace)

    nreps = draw(st.lists(nrep, min_size=dsp.shape[0], max_size=dsp.shape[0]))
    # nreps = draw(nreps)

    meta = []
    for i,n in enumerate(nreps):
        meta.extend([dsp.iloc[i,:].tolist()]*n)
    meta = pd.DataFrame(meta, columns=dsp.columns)

    p = sum(nreps)
    n = draw(nobs)
    observation = st.lists(observations, min_size=p, max_size=p)

    time = draw(st.lists(time, min_size=n, max_size=n))
    data = draw(st.lists(observation, min_size=n, max_size=n))

    data = pd.DataFrame([[t]+d for t,d in zip(time, data)])

    return popmachine.DataSet(data, meta)
