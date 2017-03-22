import argparse, logging, api
from popmachine import Machine
from operation import PlateCreate, PlateDelete, DesignList, DesignSetType, SearchOperation
from operation.server import ServerOperation
import pandas as pd
from models import Plate, Well, Design, ExperimentalDesign, Base
from sqlalchemy import Table, Column, Integer, String, Interval, MetaData, ForeignKey, Float, or_, and_

machine = None

def Init(args, warn=False):

    project = machine.session.query(Project).filter(Project.name==args.project).one_or_none()

    if project is None:
        if warn:
            logging.warning("creating new project %s"%args.project)
        project = Project(name=args.project,plates=[])
        machine.session.add(project)

    return project

def ProjectList(args):

    # project = Init(args,warn=True)

    for plate in machine.session.query(Plate).all():
        print plate

def main():

    global machine

    #############
    # Parsing

    parser = argparse.ArgumentParser(prog='popmachine',description='Growth data database management in Python.')
    parser.add_argument('--database', type=str,
                        help='location of the databse', default='.popmachine.db')
    parser.add_argument("--verbose", action='store_true')

    subparsers = parser.add_subparsers(help='command to run')

    server = subparsers.add_parser("server", help='run the server')
    server.set_defaults(func=lambda x: ServerOperation.fromArgs(machine, x).run())

    # search
    search = subparsers.add_parser("search", help='search database')
    search.add_argument("--designs", help='designs to search', nargs="*", default=[])
    search.add_argument("--values", help='values to search', nargs="*", default=[])
    search.set_defaults(func=lambda x: SearchOperation.fromArgs(machine, x).run())

    #   list
    _list = subparsers.add_parser('list', help='list plates in the database')
    _list.set_defaults(func=ProjectList)

    #   Plates
    plate = subparsers.add_parser('plate', help='plate commands')
    plate.add_argument('plate', help='name of the plate')
    plateSubparsers = plate.add_subparsers(help='plate sub-commands')

    #       create

    def designKwargs(designs):
        kw = {}
        for d,v in [s.split("=") for s in designs]:
            d = d.strip().rstrip()
            v = v.strip().rstrip()
            kw[d] = v
        return kw

    plateCreate = plateSubparsers.add_parser('create', help='create new plate')
    plateCreate.set_defaults(func=lambda x: PlateCreate.fromArgs(machine, x, createIfMissing=True, **designKwargs(x.designs)).run())
    plateCreate.add_argument("data", help='data file')
    plateCreate.add_argument("experimentalDesign", help='experimental design file')
    plateCreate.add_argument("--timeColumn",type=int,default=0)
    plateCreate.add_argument("designs", help='extra designs to apply to all wells',nargs='*')

    #       delete

    plateDelete = plateSubparsers.add_parser('delete', help='remove a plate')
    plateDelete.set_defaults(func=lambda x: PlateDelete.fromArgs(machine, x).run())

    # Design

    design = subparsers.add_parser('design', help='design commands')
    # design.add_argument('--file', help='file containing designs', type=str)
    designSubparsers = design.add_subparsers(help='design sub-commands')

    #   list

    designList = designSubparsers.add_parser("list", help='list designs')
    designList.set_defaults(func=lambda x: DesignList.fromArgs(machine, x).run())

    #   setType

    designSetType = designSubparsers.add_parser("setType", help = 'set design type')
    designSetType.add_argument("design")
    designSetType.add_argument("type")
    designSetType.set_defaults(func=lambda x: DesignSetType.fromArgs(machine,x).run())

    #############


    # run command

    args,extras = parser.parse_known_args()


    machine = Machine(args.database)

    # print args

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    args.func(args)

    machine.session.commit()

if __name__=="__main__":
    main()
