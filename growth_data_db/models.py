from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Enum, Float
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, backref

Base = declarative_base()

class Project(Base):
	__tablename__ = "projects"
	id = Column(Integer, primary_key=True)
	name = Column(String,unique=True)
	plates = relationship("Plate",back_populates="project")

class Plate(Base):
	__tablename__ = "plates"
	id = Column(Integer, primary_key=True)
	name = Column(String)
	data_table = Column(String)
	wells = relationship("Well",back_populates="plate")
	project_id = Column(Integer, ForeignKey('projects.id'))
	project = relationship("Project", back_populates="plates")

	# no two plates in the same project can share a name
	__table_args__ = (UniqueConstraint('name','project_id', name='_name_project_uc'),
                     )

	def __repr__(self):
		return "Plate: %s" % self.name

class Well(Base):
	__tablename__ = "wells"
	id = Column(Integer, primary_key=True)
	plate_id = Column(Integer, ForeignKey('plates.id'))
	plate = relationship("Plate", back_populates="wells")
	plate_number = Column(Integer)
	design_values = relationship("DesignValue",back_populates="well")

	def __repr__(self):
		return "%d, %s" % (self.plate_number,self.plate.name)

class Design(Base):
	__tablename__ = "designs"
	id = Column(Integer, primary_key=True)
	name = Column(String,unique=True)
	type = Column(Enum("str","int","float",'bool'))
	values = relationship("DesignValue",back_populates="design")

	def __repr__(self):
		return "%s (%s)" % (self.name,self.type)

class DesignValue(Base):
	__tablename__ = "design_element"
	id = Column(Integer, primary_key=True)
	design_id = Column(Integer,ForeignKey("designs.id"))
	design = relationship("Design",back_populates="values")
	well_id = Column(Integer,ForeignKey("wells.id"))
	well = relationship("Well",back_populates="design_values")
	value = Column(String)

	# each well should only have one value of any single design
	__table_args__ = (UniqueConstraint('well_id','design_id', name='_well_design_uc'),)

	def get_value(self):
		if self.design.type == 'str':
			return str(self.value)
		elif self.design.type == 'int':
			return int(self.value)
		elif self.design.type == 'float':
			return float(self.value)
		elif self.design.type == 'bool':
			return bool(self.value)

	def __repr__(self):
		return "%s %s" % (self.value,self.design.name)

class Strain(Base):
	__tablename__ = "strains"
	id = Column(Integer, primary_key=True)
	name = Column(String)
	pubmed_id = Column(Integer)
	parent_id = Column(Integer, ForeignKey('strains.id'))
	children = relationship("Strain",
			backref=backref('parent', remote_side=[id])
		)

	def __repr__(self):
		if self.parent:
			return "%s (%s)" % (self.name , self.parent.name)
		else:
			return "%s" % self.name
