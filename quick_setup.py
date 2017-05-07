import popmachine
import datetime
machine = popmachine.Machine()

now = datetime.datetime.now()

user = popmachine.models.User(
    name='overlord peter', username='peter', password='temp', permissions='admin')
project = popmachine.models.Project(
    name='testing', owner=user, submission_date=now, modified_date=now)

machine.session.add(user)
machine.session.add(project)
machine.session.commit()

plate = machine.createPlate(project, 'pseudomonas',
                            dataFile='examples/example1/pseudomonas/data.csv',
                            experimentalDesignFile='examples/example1/pseudomonas/meta.csv')

wells = machine.filter(acid='acetic', pH='7.0', strain='PA01').all()
designs = machine.session.query(popmachine.models.Design)\
    .filter(popmachine.models.Design.name.in_(['acid', 'pH', 'strain', 'mM-acid'])).all()
phenotype = popmachine.models.Phenotype(
    name='pseudomonas PA01, pH=7.0, acetic acid dosage response', owner=user, wells=wells, designs=designs, project=project)
machine.session.add(phenotype)

wells = machine.filter(acid='acetic', pH=['7.0', '6.5'], strain='PA01').all()
designs = machine.session.query(popmachine.models.Design)\
    .filter(popmachine.models.Design.name.in_(['acid', 'pH', 'strain', 'mM-acid'])).all()
phenotype = popmachine.models.Phenotype(
    name='pseudomonas PA01, pH=7.0-6.5, acetic acid dosage response',
    owner=user, wells=wells, designs=designs, project=project)
machine.session.add(phenotype)

covariates = machine.session.query(popmachine.models.Design)\
    .filter(popmachine.models.Design.name.in_(['mM-acid'])).all()
covariates[0].type = 'float'
model = popmachine.models.Model(
    phenotype=phenotype, covariates=covariates, status='queued', gp=None, queue_time=now)

machine.session.add(model)

machine.session.commit()
