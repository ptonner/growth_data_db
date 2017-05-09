from sqlalchemy import MetaData
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models

class Core(object):
    """A core object, holding necessary references to database (via sqlalchemy)"""

    def __init__(self, db):
        self.engine = create_engine(db,echo=False)
        self.Session = sessionmaker(self.engine)
        self.session = self.Session()

        models.Base.metadata.create_all(self.engine)
        self.metadata = MetaData(self.engine)
        self.metadata.reflect()

    def close(self):
        self.session.close()
        self.engine.dispose()
