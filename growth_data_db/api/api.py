from sqlalchemy import Table, Column, Integer, String, Interval, MetaData, ForeignKey, Float, or_, and_
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
import models

# engine = create_engine("sqlite:///:memory:",echo=False)
engine = create_engine("sqlite:///growth.db",echo=False)
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

	wells = [models.Well(plate=plate,plate_number=n) for n in numbers]

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

	well_numbers = [w.plate_number for w in plate.wells]

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

def _well_filter(numbers=None,plate=None,project=None,**kwargs):

	wells = session.query(models.Well)

	if numbers:
		wells = wells.filter(models.Well.plate_number.in_(numbers))

	if plate:
		if not isinstance(plate,list):
			plate = [plate]
		wells = wells.filter(models.Plate.name.in_(plate))

		# wells = wells.filter(models.Plate.name==plate)
	if project:
		wells = wells.filter(models.Project.name==project)

	return wells

def update_design(design_name,design_value,numbers=None,plate=None,project=None,design_type=None):
	wells = _well_filter(numbers,plate,project)
	add_experimental_design(design_name,design_value,*wells.all(),design_type=design_type)

def add_experimental_design(design_name,design_value,*args,**kwargs):
	# check if design exists, create if needed
	design = session.query(models.Design).filter(models.Design.name==design_name).one_or_none()
	if not design:
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

def add_chemical(chemical_name,chemical_value,*args,**kwargs):
	chemical = session.query(models.Chemical).filter(or_(models.Chemical.name==chemical_name,models.Chemical.abbreviation==chemical_name)).one_or_none()
	if not chemical:
		if not 'abbreviation' in kwargs:
			abbreviation = chemical_name
		else:
			abbreviation = kwargs['abbreviation']
		chemical = models.Chemical(name=chemical_name,abbreviation=abbreviation)
		session.add(chemical)

	session.commit()

	if not 'chemical_type' in kwargs:
		chemical_type = "concentration"
	else:
		chemical_type = kwargs['chemical_type']

	for well in args:
		if isinstance(well,models.Well):
			cv = models.ChemicalQuantity(chemical=chemical,well=well,value=chemical_value,type=chemical_type)
			session.add(cv)

			try:
				session.commit()
			except IntegrityError, e:
				# print "integrity error!"
				session.rollback()

def parse_metadata(meta,plate,project,designs=None,chemicals=None,number_column=None,strain_column=None,design_types=None,chemical_types=None):

	if designs is None:
		designs = []
	if chemicals is None:
		chemicals = []

	if design_types is None:
		design_types = {}
	if chemical_types is None:
		chemical_types = {}

	if strain_column:
		group_columns = designs+chemicals+[strain_column]
	else:
		group_columns = designs+chemicals

	if number_column is None:
		group = meta.groupby(group_columns)
	else:
		group = meta.groupby(group_columns+[number_column])

	for g,temp in group:
		if len(group_columns) == 1:
			g = [g]
		for ind,col in enumerate(group_columns):
			if number_column is None:
				numbers = temp.index.tolist()
			else:
				numbers = temp[number_column].tolist()

			if col in designs:
				_type=None
				if col in design_types:
					_type=design_types[col]
				update_design(col,g[ind],numbers,plate,project,design_type=_type)
			elif col in chemicals:
				_type=None
				if col in chemical_types:
					_type=chemical_types[col]
				update_chemical(col,g[ind],numbers,plate,project,chemical_type=_type)
			elif col == strain_column:
				raise NotImplemented("Strain parsing not implemented yet!")


def search(**kwargs):
	# wells = session.query(models.Well)
	# if 'plate' in kwargs:
	#
	# 	names = kwargs['plate']
	# 	if not isinstance(names,list):
	# 		names = [names]
	#
	# 	# plates = session.query(models.Plate).filter(models.Plate.name.in_(names))
	# 	# wells = session.query(models.Well).filter(models.Plate.id.in_(plates))
	# 	wells = wells.filter(models.Plate.name.in_(names))
	# else:
	# 	plates = None
	# 	wells = session.query(models.Well)

	wells = _well_filter(**kwargs)

	for k,v in kwargs.iteritems():

		if k == "number":
			wells = wells.filter(models.Well.number.in_(kwargs['number']))
			continue

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
