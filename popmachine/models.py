from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Enum, Float
from sqlalchemy import ForeignKey, UniqueConstraint, Table, PrimaryKeyConstraint
from sqlalchemy.orm import relationship, backref
from sqlalchemy import MetaData

Base = declarative_base()
metadata = MetaData()

# relationship between namespace and its owners (users)
# only owners of a namespace may modify it and its designs
user_namespace = Table('user_namespace', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('ns_id', Integer, ForeignKey('namespaces.id')),
    PrimaryKeyConstraint('user_id', 'ns_id')
)

project_namespace = Table("project_namespace", Base.metadata,
    Column('project_id', Integer, ForeignKey('projects.id')),
    Column('ns_id', Integer, ForeignKey('namespaces.id')),
    PrimaryKeyConstraint('project_id', 'ns_id')
)

class User(Base):
    __tablename__='users'

    id=Column(Integer, primary_key=True)
    name = Column(String)
    username = Column(String)
    password = Column(String)

    permissions = Column(Enum('admin', 'pleb'))

    def __repr__(self):
        return "User: %s" % (self.name)

class Namespace(Base):
    """A group of design variables, which can be shared across plates."""

    __tablename__ = 'namespaces'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String(500))

    owners = relationship(
        "User",
        secondary=user_namespace,
        backref="namespaces")

    def overlap(self, other):
        if not type(other) == Namespace:
            raise ValueError('must provide namespace!')

        names = [d.name for d in self.designs]
        return [d for d in other.designs if d.name in names]

    def conflictsWith(self, other):
        return len(self.overlap(other))>0

    def __repr__(self):
        return "namespace %s, owned by %s. (%d designs)" % (self.name, ','.join([o.name for o in self.owners]) , len(self.designs))

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    name = Column(String)

    owner_id = Column(Integer, ForeignKey('users.id'))
    owner = relationship("User", backref='projects')

    namespaces = relationship(
        "Namespace",
        secondary=project_namespace,
        backref="projects")

    def __repr__(self):
        return "project %s, owned by %s (%d plates)" % (self.name, self.owner.name, len(self.plates))

class Plate(Base):
    __tablename__ = "plates"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    project = relationship("Project", backref="plates")

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
    name = Column(String, nullable=False)
    description = Column(String,)
    type = Column(Enum("str","int","float",'bool'))
    values = relationship("ExperimentalDesign",back_populates="design")

    namespace_id = Column(Integer, ForeignKey('namespaces.id'))
    namespace = relationship('Namespace', backref='designs')

    __table_args__ = (UniqueConstraint('name', 'namespace_id', name='_name_ns_uc'),)

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
