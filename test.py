from sqlalchemy.exc import IntegrityError
import models, api, bioscreen
import pandas as pd

project = models.Project(name="test")
plate = models.Plate(name="test",project=project)
well = models.Well(plate=plate,number=101)
pq = models.Chemical(name="paraquat",abbreviation="pq")
pq_5mM = models.ChemicalQuantity(chemical=pq,well=well,value=5,type="concentration")
heatshift = models.Design(name="heat shift C",type="float")
heatshift_42c = models.DesignValue(design=heatshift,well=well,value=42)

api.session.add_all([project,plate,well,pq,pq_5mM,heatshift,heatshift_42c])
api.session.commit()

# try adding another chemical to the same well
print "try adding a second paraquat value to well %s" % well
pq_6mM = models.ChemicalQuantity(chemical=pq,well=well,value=6,type="concentration")
api.session.add(pq_6mM)
try:
	api.session.commit()
except IntegrityError, e:
	print "integrity error!"
	api.session.rollback()
	

#import api
#api.create_plate_data(plate)
#api.metadata.create_all(engine)

api.add_experimental_design('test design','testing',well,design_type='str')

data = pd.read_csv("data/20141221 H2O2 batch 3/20141221H2O2_batch3.csv")
plate, wells, data_table = api.create_plate_from_dataframe(data,'pq_test',data_columns=range(2,data.shape[1]),useColumnsForNumber=True,time_parse=bioscreen.convert_time)

api.update_designs(numbers=range(102,110),plate="pq_test",design_name="test",design_value="testing",design_type="str")
