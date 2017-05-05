from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Enum, Float, Date, Boolean, LargeBinary
from sqlalchemy import ForeignKey, UniqueConstraint, Table, PrimaryKeyConstraint
from sqlalchemy.orm import relationship, backref, validates
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import MetaData

import base64, os
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from flask_login import UserMixin

Base = declarative_base()
metadata = MetaData()

class User(Base, UserMixin):
    __tablename__='users'

    id=Column(Integer, primary_key=True)
    name = Column(String)
    username = Column(String(50))
    _password = Column(String(50))
    _salt = Column(LargeBinary(50))
    email = Column(String(50))
    email_confirmed = Column(Boolean, default=False)
    organization = Column(String(50))

    address = Column(String(50))
    city = Column(String(50))
    state = Column(String(50))
    country = Column(String(20))

    permissions = Column(Enum('admin', 'pleb'))

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def _set_password(self, plaintext):
        self._salt = os.urandom(16)
        kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
					length=32, salt=self._salt, iterations=100000,
					backend=default_backend())

        self._password = base64.urlsafe_b64encode(kdf.derive(plaintext))

    def is_correct_password(self, plaintext):
        kdf = PBKDF2HMAC(
					algorithm=hashes.SHA256(),
					length=32, salt=self._salt, iterations=100000,
					backend=default_backend())

        return self._password == base64.urlsafe_b64encode(kdf.derive(plaintext)).encode('utf-8')

    def __repr__(self):
        return "User: %s" % (self.name)

    @validates('email')
    def validate_email(self, key, address):
        assert '@' in address
        return address

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    name = Column(String)

    owner_id = Column(Integer, ForeignKey('users.id'))
    owner = relationship("User", backref='projects')

    submission_date = Column(Date)
    modified_date = Column(Date, doc='last modification date')

    description = Column(String(1000), doc = 'description of project')
    design = Column(String(1000), doc = 'overall design of project')

    views = Column(Integer, doc='number of views', default=0)

    published = Column(Boolean, doc='availability on website')
    citation_text = Column(String(300), doc='name of project citation, if applicable')
    citation_pmid = Column(Integer, doc='pubmed id of citation, if applicable')

    def __repr__(self):
        return "project %s, owned by %s (%d plates)" % (self.name, self.owner.name, len(self.plates))

class Plate(Base):
    __tablename__ = "plates"
    id = Column(Integer, primary_key=True)
    submission_date = Column(Date)
    modified_date = Column(Date, doc='last modification date')
    protocol = Column(String(1000), doc='description of the plate protocol')

    project_id = Column(Integer, ForeignKey('projects.id'))
    project = relationship("Project", backref="plates")

    views = Column(Integer, doc='number of views')

    name = Column(String)
    data_table = Column(String)
    wells = relationship("Well",back_populates="plate", cascade="all, delete, delete-orphan")

    def owner(self):
        return self.project.owner

    def __repr__(self):
        return "%s (%d)" % (self.name, len(self.wells))

well_experimental_design = Table('well_experimental_design', Base.metadata,
    Column('well_id', Integer, ForeignKey('wells.id')),
    Column('ed_id', Integer, ForeignKey('experimental_design.id')),
    PrimaryKeyConstraint('well_id', 'ed_id')
)

# many to many mapping of genes knocked-out in a sample
well_gene_id = Table('well_gene_id', Base.metadata,
    Column('well_id', Integer, ForeignKey('wells.id')),
    Column('pubmed_gene_id', Integer) # pubmed id to gene database
    )

class Well(Base):
    __tablename__ = "wells"
    id = Column(Integer, primary_key=True)
    plate_id = Column(Integer, ForeignKey('plates.id'))
    plate = relationship("Plate", back_populates="wells")
    plate_number = Column(Integer)

    organism_id = Column(Integer, doc='NCBI taxonomy id')

    experimentalDesigns = relationship(
        "ExperimentalDesign",
        secondary=well_experimental_design,
        back_populates="wells")

    def __repr__(self):
        return "%d, %s" % (self.plate_number,self.plate.name)

    def organism(self):
        from Bio import Entrez
        Entrez.email = 'peter.tonner@duke.edu'
        data = Entrez.read(Entrez.efetch(id = '%d'%self.organism_id, db = "taxonomy", retmode = "xml"))

        assert len(data) == 1, 'no record found or more than one found!'
        data = data[0]

        return data

class Design(Base):
    __tablename__ = "designs"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String(100), doc='details of design')
    protocol = Column(String(100), doc='protocol of design')
    type = Column(Enum("str","int","float",'bool'))
    values = relationship("ExperimentalDesign",back_populates="design")

    project_id = Column(Integer, ForeignKey('projects.id'))
    project = relationship('Project', backref='designs')

    __table_args__ = (UniqueConstraint('name', 'project_id', name='_name_project_uc'),)

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


well_phenotype = Table('well_phenotype', Base.metadata,
    Column('well_id', Integer, ForeignKey('wells.id')),
    Column('phenotype_id', Integer, ForeignKey('phenotypes.id')),
    PrimaryKeyConstraint('well_id', 'phenotype_id')
)

design_phenotype = Table('design_phenotype', Base.metadata,
	Column('design_id', Integer, ForeignKey('designs.id')),
	Column('phenotype_id', Integer, ForeignKey('phenotypes.id')),
    PrimaryKeyConstraint('design_id', 'phenotype_id')
)

class Phenotype(Base):

	__tablename__ = 'phenotypes'
	id = Column(Integer, primary_key=True)

	name = Column(String(50))
	owner_id = Column(Integer, ForeignKey('users.id'))
	owner = relationship('User', backref='phenotypes')

	project_id = Column(Integer, ForeignKey('projects.id'))
	project = relationship('Project', backref='phenotypes')

	omp_id = Column(String(10))

    # default_colorby_id = Column(Integer, ForeignKey('designs.id'))
    # default_colorby = relationship('Design')

	wells = relationship(
        "Well",
        secondary=well_phenotype,
        backref="phenotypes")

	designs = relationship(
        "Design",
        secondary=design_phenotype,
        backref="phenotypes")
