from sqlalchemy import MetaData
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .. import models

# engine = create_engine("sqlite:///:memory:",echo=False)

# def createEngine()

# engine = create_engine("sqlite:///growth.db",echo=False)
# Session = sessionmaker(engine)
# session = Session()
#
# models.Base.metadata.create_all(engine)
# metadata = MetaData()

class Core(object):

    def __init__(self, db):
        self.engine = create_engine("sqlite:///%s"%db,echo=False)
        self.Session = sessionmaker(self.engine)
        self.session = self.Session()

        models.Base.metadata.create_all(self.engine)
        self.metadata = MetaData()
        self.metadata.reflect(self.engine)
