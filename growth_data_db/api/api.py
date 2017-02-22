from sqlalchemy import Table, Column, Integer, String, Interval, MetaData, ForeignKey, Float, or_, and_
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from .. import models
import logging

# engine = create_engine("sqlite:///:memory:",echo=False)
# engine = create_engine("sqlite:///growth.db",echo=False)
# Session = sessionmaker(engine)
# session = Session()
#
# models.Base.metadata.create_all(engine)
# metadata = MetaData()

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

def add_experimental_design(core,design_name,design_value,*args,**kwargs):
	# check if design exists, create if needed
	design = core.session.query(models.Design).filter(models.Design.name==design_name).one_or_none()
	if not design:
		if not 'design_type' in kwargs:
			logging.warning("design %s does not exist, and no design_type is specified to create a new one. using str as default"%design_name)
			design_type='str'
		else:
			design_type = kwargs['design_type']

		design = models.Design(name=design_name,type=design_type)
		core.session.add(design)

	# for each well
	# check if design value exists, create if needed
	for well in args:
		if isinstance(well,models.Well):
			dv = models.ExperimentalDesign(design=design,well=well,value=design_value)
			core.session.add(dv)

	core.session.commit()

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
