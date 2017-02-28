from operation import Operation
from ...models import ExperimentalDesign, Design, Well
import itertools

class SearchOperation(Operation):

    argsKwargs = [('designs',None), ('values',None)]

    def __init__(self, core, designs, values):

        Operation.__init__(self,core)

        self.values = [v.split(",") for v in values]

        self.experimentalDesigns = {}

        self.combinations = itertools.product(*self.values)

        if len(designs) > 0:
            for d, v in zip(designs, self.values):

                if len(v)>0:
                    design = self.core.session.query(Design).filter(Design.name==d).one_or_none()
                    self.experimentalDesigns[d] = self.core.session.query(ExperimentalDesign)
                    self.experimentalDesigns[d] = self.experimentalDesigns[d].filter(ExperimentalDesign.design_id==design.id)
                    self.experimentalDesigns[d] = self.experimentalDesigns[d].filter(ExperimentalDesign.value.in_(v))
                else:
                    self.experimentalDesigns[d] = []

        self.wells = {}
        for c in self.combinations:

            # print c

            self.wells[c] = self.core.session.query(Well)

            for d,v in zip(designs, c):

                ed = self.experimentalDesigns[d].filter(ExperimentalDesign.value==v).one_or_none()

                if not ed is None:
                    self.wells[c] = self.wells[c].filter(Well.experimentalDesigns.contains(ed))
                else:
                    self.wells[c] = None
                    break

        for k in self.wells.keys():
            if self.wells[k] is None:
                del self.wells[k]
                continue
            print k


    def _run(self):

        for k,v in self.wells.iteritems():
            print k, v.count()
