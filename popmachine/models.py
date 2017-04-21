from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Enum, Float
from sqlalchemy import ForeignKey, UniqueConstraint, Table, PrimaryKeyConstraint
from sqlalchemy.orm import relationship, backref
from sqlalchemy import MetaData

Base = declarative_base()
metadata = MetaData()

class User(Base):
	__tablename__='users'

	id=Column(Integer, primary_key=True)
	name = Column(String)
	email = Column(String)
	password = Column(String)

	permissions = Column(Enum('global', 'local'))

class Project(Base):
	__tablename__ = 'projects'

	id = Column(Integer, primary_key=True)
	name = Column(String)
	user_id = Column(Integer, ForeignKey('users.id'))
	user = relationship('User', back_populates='projects')

class Plate(Base):
	__tablename__ = "plates"
	id = Column(Integer, primary_key=True)
	name = Column(String)
	data_table = Column(String)
	wells = relationship("Well",back_populates="plate", cascade="all, delete, delete-orphan")

	def __repr__(self):
		return "%s (%d)" % (self.name, len(self.wells))

well_experimental_design = Table('well_experimental_design', Base.metadata,
    Column('well_id', Integer, ForeignKey('wells.id')),
    Column('ed_id', Integer, ForeignKey('experimental_design.id')),
	PrimaryKeyConstraint('well_id', 'ed_id')
)

class Well(Base):
	__tablename__ = "wells"
	id = Column(Integer, primary_key=True)
	plate_id = Column(Integer, ForeignKey('plates.id'))
	plate = relationship("Plate", back_populates="wells")
	plate_number = Column(Integer)
	# design_values = relationship("ExperimentalDesign",back_populates="well")

	experimentalDesigns = relationship(
        "ExperimentalDesign",
        secondary=well_experimental_design,
        back_populates="wells")

	def __repr__(self):
		return "%d, %s" % (self.plate_number,self.plate.name)

class Design(Base):
	__tablename__ = "designs"
	id = Column(Integer, primary_key=True)
	name = Column(String,unique=True)
	description = Column(String,)
	type = Column(Enum("str","int","float",'bool'))
	values = relationship("ExperimentalDesign",back_populates="design")

	def __repr__(self):
		return "%s (%s)" % (self.name,self.type)

	def value(self, value):
		if self.type == 'str':
			return str(value)
		elif self.type == 'int':
			return int(value)
		elif self.type == 'float':
			return float(value)
		elif self.type == 'bool':
			return bool(value)

class ExperimentalDesign(Base):
	__tablename__ = "experimental_design"
	id = Column(Integer, primary_key=True)
	design_id = Column(Integer,ForeignKey("designs.id"))
	design = relationship("Design",back_populates="values")
	# well_id = Column(Integer,ForeignKey("wells.id"))
	# well = relationship("Well",back_populates="design_values")
	value = Column(String)

	wells = relationship(
        "Well",
        secondary=well_experimental_design,
        back_populates="experimentalDesigns")


	# each well should only have one value of any single design
	# __table_args__ = (UniqueConstraint('well_id','design_id', name='_well_design_uc'),)

	def get_value(self):
		return self.design.value(self.value)

	def __repr__(self):
		return "%s(%s)" % (self.design.name, self.value)



# class Parent(Base):
#     __tablename__ = 'left'
#     id = Column(Integer, primary_key=True)
#     children = relationship(
#         "Child",
#         secondary=association_table,
#         back_populates="parents")

# class Child(Base):
#     __tablename__ = 'right'
#     id = Column(Integer, primary_key=True)
#     parents = relationship(
#         "Parent",
#         secondary=association_table,
#         back_populates="children")
