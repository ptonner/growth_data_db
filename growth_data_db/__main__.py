import argparse, logging
from models import Project, Plate, Well, Design, ExperimentalDesign
from core import *

# logger = logging.getLogger(__name__)

def PlateCreate(args):

    project = session.query(Project).filter(Project.name==args.project).one_or_none()
    if project is None:
        logging.warning("creating new project %s"%args.project)
        project = Project(name=args.project,plates=[])
        session.add(project)

        # raise ValueError("project %s does not exist"%args.project)

    # session.commit()

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

subparsers = parser.add_subparsers(help='command to run')

init = subparsers.add_parser('init', help='initialize a project')

plate = subparsers.add_parser('plate', help='plate commands')
# plate.set_defaults(func=Plate)
plateSubparsers = plate.add_subparsers(help='plate sub-commands')

plateCreate = plateSubparsers.add_parser('create', help='create new plate')
plateCreate.add_argument('name',type=str,help='name of plate')
plateCreate.add_argument("data", help='data file')
plateCreate.add_argument("experimentalDesign", help='experimental design file')
plateCreate.set_defaults(func=PlateCreate)

# plate.add_argument('--create', action='store_true', help='create this plate')
# plate.add_argument('--data', type=str, help='data file')
# plate.add_argument('--experimentalDesign', type=str, help='experimental design file')

design = subparsers.add_parser('design', help='design commands')
design.set_defaults(func=Design)
design.add_argument('--file', help='file containing designs', type=str)

args = parser.parse_args()

if args.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

args.func(args)
