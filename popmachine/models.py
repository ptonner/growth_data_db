from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Enum, Float, Date, DateTime, Boolean, LargeBinary, PickleType, CheckConstraint, JSON
from sqlalchemy import ForeignKey, UniqueConstraint, Table, PrimaryKeyConstraint
from sqlalchemy.orm import relationship, backref, validates
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import MetaData

import GPy
import base64
import os
import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from flask_login import UserMixin

Base = declarative_base()
metadata = MetaData()


class User(Base, UserMixin):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
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

    def modelCount(self):
        return sum([len(p.models) for p in self.phenotypes])

    def __repr__(self):
        return "User: %s" % (self.name)

    @validates('email')
    def validate_email(self, key, address):
        assert '@' in address
        return address


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    nickname = Column(String(20), unique=True,
                        doc='short name used from easy reference, searching')

    owner_id = Column(Integer, ForeignKey('users.id'))
    owner = relationship("User", backref='projects')

    submission_date = Column(Date)
    modified_date = Column(Date, doc='last modification date')

    description = Column(String(1000), doc='description of project')
    design = Column(String(1000), doc='overall design of project')

    views = Column(Integer, doc='number of views', default=0)

    published = Column(Boolean, doc='availability on website')
    citation_text = Column(
        String(300), doc='name of project citation, if applicable')
    citation_pmid = Column(Integer, doc='pubmed id of citation, if applicable')

    def __repr__(self):
        return "project %s, owned by %s (%d plates)" % (self.name, self.owner.name, len(self.plates))

    def size(self):

        return sum([len(p.wells) for p in self.plates])


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
    wells = relationship("Well", back_populates="plate",
                         cascade="all, delete, delete-orphan")

    def owner(self):
        return self.project.owner

    def __repr__(self):
        return "%s (%d)" % (self.name, len(self.wells))


well_experimental_design = Table('well_experimental_design', Base.metadata,
                                 Column('well_id', Integer,
                                        ForeignKey('wells.id')),
                                 Column('ed_id', Integer, ForeignKey(
                                     'experimental_design.id')),
                                 PrimaryKeyConstraint('well_id', 'ed_id')
                                 )

# many to many mapping of genes knocked-out in a sample
well_gene_id = Table('well_gene_id', Base.metadata,
                     Column('well_id', Integer, ForeignKey('wells.id')),
                     # pubmed id to gene database
                     Column('pubmed_gene_id', Integer)
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
        return "%d, %s" % (self.plate_number, self.plate.name)

    def organism(self):
        from Bio import Entrez
        Entrez.email = 'popmachine.db@gmail.com'
        data = Entrez.read(Entrez.efetch(id='%d' %
                                         self.organism_id, db="taxonomy", retmode="xml"))

        assert len(data) == 1, 'no record found or more than one found!'
        data = data[0]

        return data


class Design(Base):
    __tablename__ = "designs"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String(100), doc='details of design')
    protocol = Column(String(100), doc='protocol of design')
    type = Column(Enum("str", "int", "float", 'bool'))
    values = relationship("ExperimentalDesign", back_populates="design")

    project_id = Column(Integer, ForeignKey('projects.id'))
    project = relationship('Project', backref='designs')

    __table_args__ = (UniqueConstraint(
        'name', 'project_id', name='_name_project_uc'),)

    def __repr__(self):
        return "%s (%s)" % (self.name, self.type)

    def value(self, value):
        if self.type == 'str':
            return unicode(value)
        elif self.type == 'int':
            return int(value)
        elif self.type == 'float':
            return float(value)
        elif self.type == 'bool':
            return bool(value)


class ExperimentalDesign(Base):
    __tablename__ = "experimental_design"
    id = Column(Integer, primary_key=True)
    design_id = Column(Integer, ForeignKey("designs.id"))
    design = relationship("Design", back_populates="values")
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
                       Column('phenotype_id', Integer,
                              ForeignKey('phenotypes.id')),
                       PrimaryKeyConstraint('well_id', 'phenotype_id')
                       )

design_phenotype = Table('design_phenotype', Base.metadata,
                         Column('design_id', Integer,
                                ForeignKey('designs.id')),
                         Column('phenotype_id', Integer,
                                ForeignKey('phenotypes.id')),
                         PrimaryKeyConstraint('design_id', 'phenotype_id')
                         )


class Phenotype(Base):

    __tablename__ = 'phenotypes'

    id = Column(Integer, primary_key=True)

    name = Column(String(50))
    owner_id = Column(Integer, ForeignKey('users.id'))
    owner = relationship('User', backref='phenotypes')

    # design space control index
    control = Column(Integer, default=0)

    project_id = Column(Integer, ForeignKey('projects.id'))
    project = relationship('Project', backref='phenotypes')

    omp_id = Column(String(7), default='0007167')
    # omp_phenotype = Column(JSON,)

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

    __table_args__ = (
        CheckConstraint(control >= 0, name='check_control_positive'),
        {})

    @hybrid_property
    def download_phenotype(self):

        url = r'http://www.ebi.ac.uk/ols/api/ontologies/omp/terms/http%%253A%%252F%%252Fpurl.obolibrary.org%%252Fobo%%252FOMP_%s'%(self.omp_id)
        r = requests.get(url)
        if r.ok:
            self.omp_phenotype = r.json()

    def dataset(self, machine):
        wells = machine.session.query(Well).filter(
            Well.id.in_([w.id for w in self.wells]))
        return machine.get(wells, include=[d.name for d in self.designs])


# determines which design variables are used as covariates for models
design_covariates = Table('design_covariates', Base.metadata,
                         Column('design_id', Integer,
                                ForeignKey('designs.id')),
                         Column('covariate_id', Integer, ForeignKey('covariates.id')),
                         PrimaryKeyConstraint('design_id', 'covariate_id')
                         )

# map covariates to models
model_covariates = Table('model_covariates', Base.metadata,
                         Column('model_id', Integer,
                                ForeignKey('models.id')),
                         Column('covariate_id', Integer, ForeignKey('covariates.id')),
                         PrimaryKeyConstraint('model_id', 'covariate_id')
                         )

class Covariate(Base):

    __tablename__ = 'covariates'
    id = Column(Integer, primary_key=True)

    designs = relationship(
        "Design",
        secondary=design_covariates,
        backref="covariates")

    models = relationship(
        "Model",
        secondary=model_covariates,
        backref="covariates")

    @hybrid_property
    def name(self):
        return ':'.join([d.name for d in self.designs])

    def kernel(self, x, ktype=GPy.kern.RBF, **kwargs):
        ind = [x.columns.index(d.name) for d in self.designs]
        return ktype(len(ind), active_dims=ind, **kwargs)

    def __repr__(self):
        return self.name

class Model(Base):

    __tablename__ = 'models'
    id = Column(Integer, primary_key=True)

    # maximum number of datapoints in model
    MAX_SIZE = 3000

    @classmethod
    def step_size(x):
        return (x.shape[0] + MAX_SIZE - 1) / MAX_SIZE

    @hybrid_property
    def log_likelihood(self):
        if self.gp:
            return self.gp.log_likelihood()
        return None

    phenotype_id = Column(Integer, ForeignKey('phenotypes.id'))
    phenotype = relationship('Phenotype', backref='models')


    # state of model training
    status = Column(Enum('unqueued', 'queued', 'training', 'trained', 'error'))

    # queue details
    queue_time = Column(DateTime)

    # step size when building input data
    step = Column(Integer, default=1)

    # number of times the model was trained
    iterations = Column(Integer, default=1)
    gp = Column(PickleType,)

    @hybrid_property
    def name(self):
        s = 'f(time)'
        for c in self.covariates:
            s += '+ f(time, %s)'%c.name
        return s

    def difference(self, other):
        return [c for c in self.covariates if not c in other.covariates], [c for c in other.covariates if not c in self.covariates]

# test for statistical significance between two models, e.g. B-GREAT bayes factor
class Test(Base):
    __tablename__='tests'
    id = Column(Integer, primary_key=True)

    phenotype_id = Column(Integer, ForeignKey('phenotypes.id'))
    phenotype = relationship('Phenotype', backref='tests')

    null_model_id = Column(Integer, ForeignKey('models.id'))
    null_model = relationship('Model', foreign_keys=[null_model_id])

    alternative_model_id = Column(Integer, ForeignKey('models.id'))
    alternative_model = relationship('Model',foreign_keys=[alternative_model_id])

    @hybrid_property
    def bayesFactor(self):

        if self.null_model and self.alternative_model:
            nmll = self.null_model.log_likelihood
            amll = self.null_model.log_likelihood
            if nmll and amll:
                return amll - nmll
        return None
