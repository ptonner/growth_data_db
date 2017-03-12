from hypothesis import given
import hypothesis.strategies as st

import popmachine, itertools
import pandas as pd
from ..utils import charstring
from operator import mul


@st.composite
def designSpace(draw, minDesigns=1, maxDesigns=3, maxTreatments=3):
    """Build a design space for testing.

    input:
        minDesigns (int): minimum number of designs possible in design space.
            Cannot be lower than 1.
        maxDesigns (int): maximum number of designs
        maxTreatments: maximum number of treatments for each design, cannot be
            lower than 1.

    output:
        designspace (pandas.DataFrame)

    A design space is defined by a pandas DataFrame. Each column is a design
    variable and each row is a unique design in the design space. This
    implementation constructs the design space by creating a list of design options
    varying from size 1 to maxTreatments. All possible design combinations are
    put into the design space dataframe (cartesian product)."""

    minDesigns = max(minDesigns, 1)
    maxDesigns = max(minDesigns, maxDesigns)
    maxTreatments = max(maxTreatments, 1)

    designSize = st.integers(min_value=1, max_value=maxTreatments)
    designSizes = draw(st.shared(\
                            st.lists(designSize, min_size=minDesigns, max_size=maxDesigns),
                            key='incomplete-designSizes'))

    designs = [draw(st.lists(st.text(charstring,min_size=1), min_size=d, max_size=d, unique=True)) for d in designSizes]
    names = draw(st.lists(charstring, min_size=len(designs), max_size=len(designs), unique=True))

    designspace = [list(x) for x in itertools.product(*designs)]
    designspace = pd.DataFrame(designspace, columns = names)

    return designspace

@st.composite
def dataset(draw, designspace=designSpace(),
            nrep=st.integers(min_value=0, max_value=3),\
            nobs=st.integers(min_value=1,max_value=100), observations=st.floats(),\
            time=st.floats(allow_infinity=False, allow_nan=False)):

    dsp = draw(designspace)

    k = dsp.shape[0]
    nreps = draw(st.lists(nrep, min_size=k, max_size=k).filter(lambda x: sum(x)>0))

    meta = []
    for i,n in enumerate(nreps):
        meta.extend([dsp.iloc[i,:].tolist()]*n)
    meta = pd.DataFrame(meta, columns=dsp.columns)

    p = sum(nreps)
    n = draw(nobs)
    observation = st.lists(observations, min_size=p, max_size=p)

    time = draw(st.lists(time, min_size=n, max_size=n, unique=True))
    data = draw(st.lists(observation, min_size=n, max_size=n))

    data = pd.DataFrame([[t]+d for t,d in zip(time, data)])

    return popmachine.DataSet(data, meta)

sharedDesignSpace = st.shared(designSpace(), key='incomplete-designspace')

@st.composite
def compendia(draw,designspace=sharedDesignSpace,
            nrep=st.integers(min_value=0,max_value=3),\
            nobs=st.integers(min_value=1,max_value=50), observations=st.floats(),\
            time=st.floats(allow_infinity=False, allow_nan=False)):

    """Create a list of datasets all created from a shared design space."""

    n = draw(st.integers(min_value=2, max_value=5))
    ds = dataset(designspace, nrep, nobs, observations, time)
    datasets = draw(st.lists(ds, min_size=n, max_size=n))
    names = draw(st.lists(charstring, min_size=n, max_size=n, unique=True))

    return names, datasets
