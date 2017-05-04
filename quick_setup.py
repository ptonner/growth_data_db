import popmachine, datetime
machine = popmachine.Machine()

now = datetime.datetime.now()

user = popmachine.models.User(name='overlord peter', username='peter', password='temp')
project = popmachine.models.Project(name='testing', owner=user,submission_date=now, modified_date=now)

machine.session.add(user)
machine.session.add(project)
machine.session.commit()
