from sqlalchemy.orm import aliased
from ..models import Well, ExperimentalDesign, well_experimental_design
import pandas as pd


def design_space(session, phenotype):
    """Compute the design space of a phenotype."""

    # make an alias of experimental design for each Design
    # and build a query selecting on these aliases
    designs = phenotype.designs
    values = [aliased(ExperimentalDesign) for d in designs]
    wells = [aliased(Well) for d in designs]
    q = session.query(*values)

    for a, wa, d in zip(values, wells, designs):
        q = q.filter(a.design == d)
        q = q.join(wa, a.wells)
        q = q.filter(wa.id.in_([w.id for w in phenotype.wells]))

    # cut down the search space to something sane
    wa0 = wells[0]
    for wa in wells[1:]:
        q = q.filter(wa.id == wa0.id)

    q = q.all()

    return q


def designSpace(session, phenotype):

    q = design_space(session, phenotype)

    dsp = pd.DataFrame([[v.get_value() for v in b]
                        for b in q], columns=[d.name for d in phenotype.designs])
    return dsp
