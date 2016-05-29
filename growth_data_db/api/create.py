from ..core import *

def create(project=None):
	if not project is None:
		if type(project) == dict:
			_create_project(**project)

def _create_project(name=None,plates=[]):
	project = models.Project(name=name,plates=plates)
	session.add(project)
	session.commit()
