import argparse, logging, core, api
from core import PlateCreate
import pandas as pd
from models import Project, Plate, Well, Design, ExperimentalDesign, Base
from sqlalchemy import Table, Column, Integer, String, Interval, MetaData, ForeignKey, Float, or_, and_

# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

def Init(args, warn=False):

    project = core.session.query(Project).filter(Project.name==args.project).one_or_none()

    if project is None:
        if warn:
            logging.warning("creating new project %s"%args.project)
        project = Project(name=args.project,plates=[])
        core.session.add(project)

    return project

def ProjectList(args):

    project = Init(args,warn=True)

    for plate in project.plates:
        print plate

class PlateCommand(object):

    def __init__(self,args):
        self.args = args

        self.project = core.session.query(Project).filter(Project.name==args.project).one_or_none()
        if self.project is None:
            logging.warning("creating new project %s"%self.args.project)
            self.project = Project(name=args.project,plates=[])
            core.session.add(self.project)

        self.plate = core.session.query(Plate).filter(Plate.name==args.plate, Plate.project==self.project).one_or_none()

    def run(self):
        self._run()

    def _run(self):
        raise NotImplemented()

class PlateDelete(PlateCommand):

    def _run(self):
        if not self.plate is None:
            if not self.plate.data_table is None:
                core.metadata.tables[self.plate.data_table].drop(core.engine)
            core.session.delete(self.plate)

# def PlateCreate(args):
#
#     project = core.session.query(Project).filter(Project.name==args.project).one_or_none()
#     if project is None:
#         logging.warning("creating new project %s"%args.project)
#         project = Project(name=args.project,plates=[])
#         core.session.add(project)
#
#     plate = core.session.query(Plate).filter(Plate.name==args.plate, Plate.project==project).one_or_none()
#     if not plate is None:
#         logging.error("plate named %s already exists in project %s!"%(args.plate, args.project))
#         return
#
#     plate = Plate(name=args.plate,project=project)
#     core.session.add(plate)
#     core.session.commit()
#
#     data = pd.read_csv(args.data)
#     meta = pd.read_csv(args.experimentalDesign)
#
#     data_columns = range(data.shape[1])
#     data_columns.remove(args.timeColumn)
#
#     wells = [Well(plate=plate,plate_number=n) for n in data_columns]
#     core.session.add_all(wells)
#     core.session.commit()
#
#     table = api.upload.create_plate_data_table(plate,core)
#     core.session.commit()
#
#     # copy in data
#     conn = core.engine.connect()
#     ins = table.insert()
#
# 	# add each row to the table
#     for i in range(data.shape[0]):
#         newrow = dict([('time',data.iloc[i,0])] + [(str(j),data.iloc[i,j]) for j in data_columns])
#         conn.execute(ins,**newrow)
#
#     # add experimental designs
#     for c in meta.columns:
#         for u in meta[c].unique():
#             select = meta[c] == u
#             temp = [w for w,s in zip(wells, select.tolist()) if s]
#             api.add_experimental_design(core,c,u,*temp)

def Design(args):
    pass


"""
main
    plate
        create
    design
"""

parser = argparse.ArgumentParser(prog='growthdatadb',description='Growth data database management in Python.')
parser.add_argument('database', type=str,
                    help='location of the databse')
parser.add_argument('project', type=str,
                    help='project in the database')
parser.add_argument("--verbose", action='store_true')
parser.add_argument("--commit", action='store_true')

subparsers = parser.add_subparsers(help='command to run')

init = subparsers.add_parser('init', help='initialize a project')
init.set_defaults(func=Init)

init = subparsers.add_parser('list', help='list plates in a project')
init.set_defaults(func=ProjectList)

plate = subparsers.add_parser('plate', help='plate commands')
plate.add_argument('plate', help='name of the plate')
plateSubparsers = plate.add_subparsers(help='plate sub-commands')

plateCreate = plateSubparsers.add_parser('create', help='create new plate')
plateCreate.set_defaults(func=lambda x: PlateCreate(core, x.project, x.plate, x.data, x.experimentalDesign, createIfMissing=True).run())
# plateCreate.set_defaults(func=PlateCreate)
# plateCreate.add_argument('name',type=str,help='name of plate')
plateCreate.add_argument("data", help='data file')
plateCreate.add_argument("experimentalDesign", help='experimental design file')
plateCreate.add_argument("--timeColumn",type=int,default=0)

plateDelete = plateSubparsers.add_parser('delete', help='remove a plate')
plateDelete.set_defaults(func=lambda x: PlateDelete(x).run())


# plate.add_argument('--create', action='store_true', help='create this plate')
# plate.add_argument('--data', type=str, help='data file')
# plate.add_argument('--experimentalDesign', type=str, help='experimental design file')

design = subparsers.add_parser('design', help='design commands')
design.set_defaults(func=Design)
design.add_argument('--file', help='file containing designs', type=str)

args = parser.parse_args()

# engine = create_engine("sqlite:///%s"%args.database,echo=False)
# Session = sessionmaker(engine)
# session = Session()
#
# Base.metadata.create_all(engine)
# metadata = MetaData()
core = core.Core(args.database)

if args.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

args.func(args)

# if args.commit:
core.session.commit()
