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
        wells = wells.join(designAlias, valueAlias.design)

        if isinstance(v, list):
            # convert non-string values
            # v = [str(z) for z in v]

            wells = wells.filter(or_(
                                        ~exists().where(designAlias.name==d),
                                        or_(
                                            and_(designAlias.name==d, designAlias.type=='str', valueAlias.value.in_(v)),
                                            and_(designAlias.name==d, designAlias.type=='int', cast(valueAlias.value, Integer).in_(v)),
                                            and_(designAlias.name==d, designAlias.type=='float', cast(valueAlias.value, Float).in_(v)),
                                        )
                                    )
                                )

        else:
            # convert non-string values
            # v = str(v)

            wells = wells.filter(or_(
                                        ~exists().where(designAlias.name==d),
                                        # and_(designAlias.name==d, valueAlias.value==v)
                                        or_(
                                            and_(designAlias.name==d, designAlias.type=='str', valueAlias.value==v),
                                            and_(designAlias.name==d, designAlias.type=='int', cast(valueAlias.value, Integer)==v),
                                            and_(designAlias.name==d, designAlias.type=='float', cast(valueAlias.value, Float)==v),
                                        )
                                    )
                                )

    return wells
