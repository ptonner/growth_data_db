import popmachine, itertools
from hypothesis import given
import hypothesis.strategies as st

import unittest
import numpy as np

# stop telling me about comparing NaN's!!!
np.seterr(invalid='ignore')

# machine = popmachine.Machine('.test.db')
# machine = popmachine.Machine(':memory:')

# utility for making character string with limited range
simplechars = st.characters(min_codepoint=1, max_codepoint=100, blacklist_categories=('Cc', 'Cs'))
charstring = st.text(simplechars, min_size=1)

# platename = st.text(simplechars, min_size=5).filter(lambda x: not x in machine.plates(names=True))
platename = st.text(simplechars, min_size=5)

class StatelessDatabaseTest(unittest.TestCase):
    """"Base class for database tests that destroy their operation on completion."""

    #setup/teardown_example is called each time by hypothesis, as opposed to setUp
    def setup_example(self,):
        self.machine = popmachine.Machine(":memory:")
        self.project = popmachine.models.Project(name='testing')
        self.machine.session.add(self.project)
        self.machine.session.commit()

    # def teardown_example(self):
    #     self.machine.close()
