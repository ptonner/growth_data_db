from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, Float, or_, and_
import models

metadata = MetaData()

def create_plate_from_dataframe(data,name,conn):
	plate = models.Plate(name=name)
	
	wells = [models.Well(plate=plate,number=data.columns[i]) for i in range(1,data.shape[1])]
	
	table = create_plate_data_table(plate)
	copy_plate_dataframe_to_table(data,table,conn)
	
	return plate,wells,table

def create_plate_data_table(plate):
	well_numbers = [w.number for w in plate.wells]
		
	cols = [Column('id', Integer, primary_key=True), Column('time', Float)] + \
		[Column('well_%d'%wn, Float) for wn in well_numbers]
		
	table = Table("_plate_data_%d"%plate.id,metadata,*cols)
	return table
	
def copy_plate_dataframe_to_table(data,table,conn):
	
	ins = table.insert()
	
	# add each row to the table
	for i in range(data.shape[0]):
		newrow = dict([('time',data.iloc[i,0])] + [(data.columns[j],data.iloc[i,j]) for j in range(1,data.shape[1])])
		conn.execute(ins,**newrow)
		
def search(session,**kwargs):
	if 'plate' in kwargs:
		plates = session.query(models.Plate).filter(models.Plate.name.in_(kwargs['plates']))
		wells = session.query(models.Well).filter(model.Plate.id.in_(plates))
	else:
		plates = None
		wells = session.query(models.Well)
		
	for k,v in kwargs.iteritems():
	
		# if design exists matching key, filter by value
		design = session.query(models.Design).filter(models.Design.name==k).one_or_none()
		
		# only search if design exists
		if design:
			wells = wells.filter(and_(
						  # check kwarg key against name and abbreviation of design
						  models.Design.name == k,
						  # check value equality
						  models.DesignValue.value==v
						  ))
						  
		# if chemical exists matching key, filter by value
		chemical = session.query(models.Chemical).filter(models.Chemical.name==k).one_or_none()
		
		# only search if chemical exists
		if chemical:
			wells = wells.filter(and_(
						  # check kwarg key against name and abbreviation of chemical
						  or_(models.Chemical.name == k,models.Chemical.abbreviation == k),
						  # check value equality
						  models.ChemicalQuantity.value==v
						  ))
					  
	# filter wells by chemical concentrations matching kwarg name and value
	
	return wells
