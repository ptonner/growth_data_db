from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, Float

metadata = MetaData()

def create_plate_data(plate):
	well_numbers = [w.number for w in plate.wells]
		
	cols = [Column('id', Integer, primary_key=True), Column('time', Float)] + \
		[Column('well_%d'%wn, Float) for wn in well_numbers]
		
	table = Table("_plate_data_%d"%plate.id,metadata,*cols)
	
