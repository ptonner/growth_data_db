from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
import models

engine = create_engine("sqlite:///:memory:",echo=True)
Session = sessionmaker(engine)
session = Session()

models.Base.metadata.create_all(engine)

project = models.Project(name="test")
plate = models.Plate(name="test",project=project)
well = models.Well(plate=plate,number=101)
pq = models.Chemical(name="paraquat",abbreviation="pq")
pq_5mM = models.ChemicalQuantity(chemical=pq,well=well,value=5,type="concentration")
heatshift = models.Design(name="heat shift C",type="float")
heatshift_42c = models.DesignValue(design=heatshift,well=well,value=42)

session.add_all([project,plate,well,pq,pq_5mM,heatshift,heatshift_42c])
session.commit()

# try adding another chemical to the same well
print "try adding a second paraquat value to well %s" % well
pq_6mM = models.ChemicalQuantity(chemical=pq,well=well,value=6,type="concentration")
session.add(pq_6mM)
try:
	session.commit()
except IntegrityError, e:
	print "integrity error!"
	session.rollback()
	

#import api
#api.create_plate_data(plate)
#api.metadata.create_all(engine)

