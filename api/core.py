from sqlalchemy import MetaData
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models

# engine = create_engine("sqlite:///:memory:",echo=False)
engine = create_engine("sqlite:///growth.db",echo=False)
Session = sessionmaker(engine)
session = Session()

models.Base.metadata.create_all(engine)
metadata = MetaData()
