import popmachine
import datetime
import os

machine = popmachine.Machine()

now = datetime.datetime.now()

user = popmachine.models.User(
    name='overlord peter', username='peter', password='temp', permissions='admin')
project = popmachine.models.Project(
    name='testing', owner=user, submission_date=now, modified_date=now)

machine.session.add(user)
machine.session.add(project)
machine.session.commit()

# plate = machine.createPlate(project, 'PA01-acetic',
#                             dataFile='examples/example1/pseudomonas/PA01-acetic/data.csv',
#                             experimentalDesignFile='examples/example1/pseudomonas/PA01-acetic/meta.csv')


for p in os.listdir('examples/example1/pseudomonas'):
    machine.createPlate(project, p,
                            dataFile='examples/example1/pseudomonas/%s/data.csv'%p,
                            experimentalDesignFile='examples/example1/pseudomonas/%s/meta.csv'%p)

# ph 7
wells = machine.filter(acid='acetic', pH='7.0', strain='PA01').all()
designs = machine.session.query(popmachine.models.Design)\
    .filter(popmachine.models.Design.name.in_(['acid', 'pH', 'strain', 'mM-acid'])).all()
phenotype = popmachine.models.Phenotype(
    name='pseudomonas PA01, pH=7.0, acetic acid dosage response', owner=user, wells=wells, designs=designs, project=project)
phenotype.download_phenotype()
machine.session.add(phenotype)

model = popmachine.models.Model(
    phenotype=phenotype, status='queued', gp=None, queue_time=now)
covariate = popmachine.models.Covariate(designs=machine.session.query(popmachine.models.Design)\
    .filter(popmachine.models.Design.name.in_(['mM-acid'])).all())
covariate.models.append(model)

nullmodel = popmachine.models.Model(
    phenotype=phenotype, status='queued', gp=None, queue_time=now)

test = popmachine.models.Test(phenotype=phenotype, null_model=nullmodel, alternative_model=model)

machine.session.add_all([model, covariate, nullmodel, test])

# ph 7, 6.5
wells = machine.filter(acid='acetic', pH=['7.0', '6.5'], strain='PA01').all()
designs = machine.session.query(popmachine.models.Design)\
    .filter(popmachine.models.Design.name.in_(['acid', 'pH', 'strain', 'mM-acid'])).all()
phenotype = popmachine.models.Phenotype(
    name='pseudomonas PA01, pH=7.0-6.5, acetic acid dosage response',
    owner=user, wells=wells, designs=designs, project=project)
phenotype.download_phenotype()
machine.session.add(phenotype)


# model = popmachine.models.Model(
#     phenotype=phenotype, status='queued', gp=None, queue_time=now)
#
# covariate = popmachine.models.Covariate(designs=machine.session.query(popmachine.models.Design)\
#     .filter(popmachine.models.Design.name.in_(['mM-acid'])).all())
# covariate.models.append(model)

machine.session.add(model)
machine.session.add(covariate)

machine.session.commit()
