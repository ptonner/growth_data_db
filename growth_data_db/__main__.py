import argparse
from models import Project, Plate, Well, Design, ExperimentalDesign
from core import *

def Plate(args):

    project = session.query(Project).filter(Project.name==args.project).one_or_none()
    if project is None:
        #project = create.create(project={'name':args.project})
        raise ValueError("project %s does not exist"%args.project)

    if args.create:
        pass
    if args.data:
        pass
    if args.experimentalDesign:
        pass

def Design(args):
    pass

parser = argparse.ArgumentParser(prog='growthdatadb',description='Growth data database management in Python.')
parser.add_argument('database', type=str,
                    help='location of the databse')
parser.add_argument('project', type=str,
                    help='project in the database')

subparsers = parser.add_subparsers(help='command to run')

init = subparsers.add_parser('init', help='initialize a project')

plate = subparsers.add_parser('plate', help='plate commands')
plate.set_defaults(func=Plate)
plate.add_argument('name',type=str,help='name of plate')
plate.add_argument('--create', action='store_true', help='create this plate')
plate.add_argument('--data', type=str, help='data file')
plate.add_argument('--experimentalDesign', type=str, help='experimental design file')

design = subparsers.add_parser('design', help='design commands')
design.set_defaults(func=Design)
design.add_argument('--file', help='file containing designs', type=str)

args = parser.parse_args()
args.func(args)
