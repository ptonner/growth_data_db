from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
import models

engine = create_engine("sqlite:///:memory:",echo=False)
Session = sessionmaker(engine)
session = Session()

models.Base.metadata.create_all(engine)

project = models.Project(name="test")
plate = models.Plate(name="test",project=project)
well = models.Well(plate=plate,number=101)
pq = models.Chemical(name="paraquat",abbreviation="pq")
pq_5mM = models.ChemicalQuantity(chemical=pq,well=well,value=5,type="concentration")

session.add_all([project,plate,well,pq,pq_5mM])
session.commit()

# try adding another chemical to the same well
pq_6mM = models.ChemicalQuantity(chemical=pq,well=well,value=6,type="concentration")
session.add(pq_6mM)
try:
	session.commit()
except IntegrityError, e:
	print "integrity error!"
	session.rollback()

