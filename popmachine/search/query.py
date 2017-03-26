from sqlalchemy.sql.expression import cast
from sqlalchemy import String, Integer, Boolean, Float, and_, or_, exists
from ..models import Design, ExperimentalDesign, Well
from sqlalchemy.orm import aliased

def query(wells, **kwargs):

    """Given a query on wells, filter by design=value provided in kwargs."""

    for d, v in kwargs.iteritems():

        valueAlias = aliased(ExperimentalDesign)
        designAlias = aliased(Design)

        wells = wells.join(valueAlias, Well.experimentalDesigns)
        wells = wells.join(designAlias)

        if isinstance(v, list):
            # convert non-string values
            v = [str(z) for z in v]

            # wells = wells.filter(and_(valueAlias.design_id==design.id, valueAlias.value.in_(v)))
            wells = wells.filter(or_(
                                        ~exists().where(designAlias.name==d),
                                        and_(designAlias.name==d, valueAlias.value.in_(v))
                                    )
                                )

        else:
            # convert non-string values
            v = str(v)
            # wells = wells.filter(and_(valueAlias.design_id==design.id, valueAlias.value==v))
            wells = wells.filter(or_(
                                        ~exists().where(designAlias.name==d),
                                        and_(designAlias.name==d, valueAlias.value==v)
                                    )
                                )

    return wells
