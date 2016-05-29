from .core import *

from sqlalchemy import Table, Column, Integer, String, Interval, MetaData, ForeignKey, Float, or_, and_

def create_plate_from_dataframe(dataframe,plate_name,project_name,time_column=None,data_columns=None,useColumnsForNumber=False,time_parse=None):
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

	project = session.query(models.Project).filter(models.Project.name==project_name).one()

	plate = models.Plate(name=plate_name,project=project)
	session.add(plate)
	session.commit()

	numbers = range(len(data_columns))
	if useColumnsForNumber:
		numbers = dataframe.columns[data_columns]

	wells = [models.Well(plate=plate,plate_number=n) for n in numbers]

	session.add_all(wells)
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
