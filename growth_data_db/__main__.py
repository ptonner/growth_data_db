import argparse

def plate(args):
    pass

def Design(args):
    pass

parser = argparse.ArgumentParser(prog='growthdatadb',description='Growth data database management in Python.')
parser.add_argument('database', type=str,
                    help='location of the databse')
parser.add_argument('project', type=str,
                    help='project in the database')

subparsers = parser.add_subparsers(help='command to run')

plate = subparsers.add_parser('plate', help='plate commands')
plate.add_argument('name',type=str,help='name of plate')
plate.add_argument('--create', action='store_true', help='create this plate')
plate.add_argument('--data', type=str, help='data file')
plate.set_defaults(func=plate)

design = subparsers.add_parser('design', help='design commands')
design.set_defaults(func=Design)
design.add_argument('plate', help='plate this design belongs to')
design.add_argument('file', help='file containing designs')

args = parser.parse_args()
args.func(args)
