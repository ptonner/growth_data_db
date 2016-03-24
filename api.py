from sqlalchemy import Table, Column, Integer, String, Interval, MetaData, ForeignKey, Float, or_, and_
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models

engine = create_engine("sqlite:///:memory:",echo=False)
Session = sessionmaker(engine)
session = Session()

models.Base.metadata.create_all(engine)
metadata = MetaData()

def create_plate_from_dataframe(dataframe,plate_name,time_column=None,data_columns=None,useColumnsForNumber=False,time_parse=None):
	"""Build a plate from a dataframe.
	
	Create a plate from the provided dataframe, copying data into the associated data_table.
	Specifics of which columns of the dataframe to use, for time and od, are optional arguments.
	A function for converting the time column into the timedelta type is another optional argument.
	
	Args:
		dataframe: Pandas dataframe to be copied into the database
		plate_name: name for the new plate being created
		time_column: integer index of column to use for time values
		data_columns: array of integers to use as indices for OD data
		useColumnsForNumber: if true, use the column names to specify the well number and column names in data_table
		time_parse: function used to convert time column values into timedelta
		
	Returns:
		(plate, wells, data_table): The newly created plate, its wells, and data_table with copied data from the dataframe."""
	
	if time_column is None:
		time_column = 0
		
	if time_parse:
		dataframe.iloc[:,time_column] = time_parse(dataframe.iloc[:,time_column])
	
	if data_columns is None:
		data_columns = range(dataframe.shape[1])
		data_columns.remove(time_column)
		
	assert len(data_columns) + 1 <= dataframe.shape[1], 'too many columns specified!'

	plate = models.Plate(name=plate_name)
	
	numbers = range(len(data_columns))
	if useColumnsForNumber:
		numbers = dataframe.columns[data_columns]
	
	wells = [models.Well(plate=plate,number=n) for n in numbers]
	
	session.add_all([plate]+wells)
	session.commit()
	
	table = create_plate_data_table(plate)
	
	column_names = [str(x) for x in data_columns]
	if useColumnsForNumber:
		column_names = [str(dataframe.columns[i]) for i in data_columns]
	copy_plate_dataframe_to_table(dataframe,table,data_columns,column_names)
	
	return plate,wells,table

def create_plate_data_table(plate):
	"""create a data_table for the provided plate, doing nothing if it already exists."""
	
	if not plate.data_table is None:
		return metadata.tables[plate.data_table]
	
	well_numbers = [w.number for w in plate.wells]
		
	cols = [Column('id', Integer, primary_key=True), Column('time', Interval)] + \
		[Column(str(wn), Float) for wn in well_numbers]
		
		
	table = Table("_plate_data_%d"%plate.id,metadata,*cols)
	metadata.create_all(engine)
	
	plate.data_table = table.name
	session.add(plate)
	session.commit()
	
	return table
	
def copy_plate_dataframe_to_table(data,table,data_columns,column_names):
	
	conn = engine.connect()
	ins = table.insert()
	
	# add each row to the table
	for i in range(data.shape[0]):
		newrow = dict([('time',data.iloc[i,0])] + [(cn,data.iloc[i,j]) for cn,j in zip(column_names,data_columns)])
		conn.execute(ins,**newrow)
		
def update_designs(numbers=None,plate=None,project=None,design_name=None,design_value=None,design_type=None):
	wells = session.query(models.Well)
	
	if numbers:
		wells = wells.filter(models.Well.number.in_(numbers))
	
	if plate:
		wells = wells.filter(models.Plate.name==plate)
	if project:
		wells = wells.wells.filter(models.Project.name==project)
		
	if design_name and design_value:
		add_experimental_design(design_name,design_value,wells.all(),design_type=design_type)
		
def add_experimental_design(design_name,design_value,*args,**kwargs):
	# check if design exists, create if needed
	design = session.query(models.Design).filter(models.Design.name==design_name).one_or_none()
	if not design :
		if not 'design_type' in kwargs:
			raise LookupError("design does not exist, and no design_type is specified to create a new one!")
		else:
			design = models.Design(name=design_name,type=kwargs['design_type'])
			session.add(design)
	
	# for each well
	# check if design value exists, create if needed 
	for well in args:
		if isinstance(well,models.Well):
			dv = models.DesignValue(design=design,well=well,value=design_value)
			session.add(dv)
			
	session.commit()
		
def search(**kwargs):
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
