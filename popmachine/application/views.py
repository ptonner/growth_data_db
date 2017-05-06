from app import app, mail
from popmachine import Machine, models
from .forms import SearchForm, PlateCreate, DesignForm, LoginForm, ProjectForm, PhenotypeForm, RegisterForm
from .plot import plotDataset
from ..phenotype import design_space
from safeurl import is_safe_url
from security import ts

import re, flask, datetime
import pandas as pd
from flask import Flask, render_template, request, jsonify, url_for, redirect, flash, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_mail import Message
from sqlalchemy import or_, not_
from wtforms import SelectField, StringField, TextAreaField

from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.charts import TimeSeries
from bokeh.resources import INLINE
from bokeh.util.string import encode_utf8
from bokeh.palettes import Spectral11, viridis

machine = Machine()
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return machine.session.query(models.User).filter_by(id=user_id).one_or_none()

@app.route('/')
def index():

    if not current_user.is_authenticated:
        projects = machine.session.query(models.Project).filter_by(published=True).all()
        plates = machine.session.query(models.Plate).join(models.Project).filter(models.Project.published).all()
        designs = machine.session.query(models.Design).join(models.Project).filter(models.Project.published).all()

        phenotypes = machine.session.query(models.Phenotype).join(models.Project).filter(models.Project.published).all()

    else:
        projects = machine.session.query(models.Project).filter(or_(models.Project.owner ==current_user, models.Project.published)).all()
        plates = machine.session.query(models.Plate).join(models.Project).filter(models.Project.owner==current_user).all()
        designs = machine.session.query(models.Design).join(models.Project).filter(or_(models.Project.owner ==current_user, models.Project.published)).all()

        phenotypes = machine.session.query(models.Phenotype).join(models.Project).filter(or_(models.Project.owner==current_user, models.Project.published)).all()

    if len(projects) > 5:
        projects = projects[:5]
    if len(plates) > 5:
        plates = plates[:5]
    if len(designs) > 5:
        designs = designs[:5]
    if len(phenotypes) > 5:
        phenotypes = phenotypes[:5]

    searchform = SearchForm()

    return render_template("index.html", projects=projects, plates=plates, designs=designs, phenotypes=phenotypes, searchform=searchform)

@app.route('/account/register', methods=["GET", "POST"])
def create_account():
    searchform = SearchForm()
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_confirm.data:
            flask.flash('passwords do not match!')
            return redirect(url_for('create_account'), method='GET')

        # print type(form.password.data)

        user = models.User(
            username = form.username.data,
            email = form.email.data,
            password = form.password.data.encode('utf-8')
        )
        machine.session.add(user)
        machine.session.commit()

        # Now we'll send the email confirmation link
        subject = "Confirm your email"

        token = ts.dumps(user.email, salt='email-confirm-key')

        confirm_url = url_for(
            'confirm_email',
            token=token,
            _external=True)

        html = render_template(
            'accounts/email-activate.html',
            confirm_url=confirm_url, searchform=searchform)

        # We'll assume that send_email has been defined in myapp/util.py
        msg = Message(subject,
                  sender="popmachine.db@gmail.com",
                  recipients=[user.email], html=html)
        mail.send(msg)

        print user.email, html

        # send_email(user.email, subject, html)

        return redirect(url_for("index"))

    return render_template("accounts/create.html", form=form, searchform=searchform)

@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = ts.loads(token, salt="email-confirm-key", max_age=86400)
    except:
        abort(404)

    user = machine.session.query(models.User).filter_by(email=email).one_or_none()

    if user is None:
        flask.abort(404)

    user.email_confirmed = True

    machine.session.add(user)
    machine.session.commit()

    return redirect(url_for('signin'))

@app.route('/bgreat')
def bgreat():
    searchform = SearchForm()
    return render_template("bgreat.html", searchform=searchform)

@app.route('/project/<projectid>')
def project(projectid):
    searchform = SearchForm()
    project = machine.session.query(models.Project).filter_by(id=projectid).one_or_none()

    if not project or (not project.published and (not current_user.is_authenticated or project.owner != current_user)):
        flask.flash('project not found or you do not have permissions to view it!')
        return redirect(url_for('index'))

    return render_template("project.html", project=project, searchform = searchform)

@app.route('/projects/')
def projects():

    if not current_user.is_authenticated:
        myprojects = None
        projects = machine.session.query(models.Project).filter_by(published=True)
    else:
        myprojects = machine.session.query(models.Project).filter_by(owner=current_user)
        projects = machine.session.query(models.Project).filter_by(published=True).filter(not_(models.Project.owner==current_user))

    searchform = SearchForm()

    return render_template("projects.html", myprojects=myprojects, searchform=searchform, projects=projects)

@app.route('/project/<projectid>/publish')
@login_required
def project_publish(projectid):

    project = machine.session.query(models.Project).filter_by(id=projectid, owner=current_user).one_or_none()

    if project:

        project.published = True
        machine.session.add(project)
        machine.session.commit()

        return redirect((url_for('project', projectid=project.id)))

    return redirect(url_for('projects'))

@app.route('/project/<projectid>/unpublish')
@login_required
def project_unpublish(projectid):

    project = machine.session.query(models.Project).filter_by(id=projectid, owner=current_user).one_or_none()

    if project:

        project.published = False
        machine.session.add(project)
        machine.session.commit()

        return redirect((url_for('project', projectid=project.id)))

    return redirect(url_for('projects'))


@app.route('/project-create/', methods=['GET', "POST"])
@login_required
def project_create():

    searchform = SearchForm()
    form = ProjectForm()

    if request.method=="GET":
        return render_template("project-create.html", form=form, searchform = searchform)
    else:

        # print request.form

        name = request.form['name']
        description = request.form['description']
        design = request.form['design']
        published = 'published' in request.form and request.form['published']
        citation = request.form['citation']
        citation_pmid = request.form['citation_pmid']

        now = datetime.datetime.now()

        project = models.Project(name=name, description=description, design=design, published=published, citation_text=citation, citation_pmid=citation_pmid, owner=current_user, submission_date=now, modified_date=now)
        machine.session.add(project)
        machine.session.commit()

        return redirect(url_for('project', projectid=project.id))
    return redirect(url_for('project_create'))

@app.route('/plates/')
def plates():

    if current_user.is_authenticated:
        plates = machine.session.query(models.Plate).join(models.Project).filter(or_(models.Project.published, models.Project.owner==current_user)).all()
    else:
        plates = machine.session.query(models.Plate).join(models.Project).filter(models.Project.published).all()


    searchform = SearchForm()

    return render_template("plates.html", plates=plates, searchform=searchform)

@app.route('/plate/<platename>')
def plate(platename):
    searchform = SearchForm()
    plate = machine.session.query(models.Plate).filter(models.Plate.name==platename).one_or_none()

    experimentalDesigns = machine.session.query(models.ExperimentalDesign)\
                .join(models.well_experimental_design)\
                .join(models.Well)\
                .filter(models.Well.id.in_([w.id for w in plate.wells]))

    designs = machine.session.query(models.Design)\
                .join(models.ExperimentalDesign)\
                .join(models.well_experimental_design)\
                .join(models.Well)\
                .filter(models.Well.id.in_([w.id for w in plate.wells]))

    return render_template("plate.html", plate=plate, experimentalDesigns=experimentalDesigns, designs=designs, searchform = searchform)

@app.route('/plate-delete/<platename>', methods=['GET', 'POST'])
def plate_delete(platename):
    searchform = SearchForm()

    if request.method=='GET':
        return render_template('plate-delete.html', searchform = searchform, platename=platename)
    else:
        plate = machine.session.query(models.Plate).filter(models.Plate.name==platename).one_or_none()
        machine.deletePlate(plate)

        return redirect(url_for('plates'))

@app.route('/plate-create/', methods=['GET', "POST"])
@login_required
def plate_create():

    searchform = SearchForm()

    myprojects = machine.session.query(models.Project).filter_by(owner=current_user).all()

    class DynamicPlateCreate(PlateCreate):
        project = SelectField("project", choices=[(p.name, p.name) for p in myprojects])

    if request.method=="GET":
        form = DynamicPlateCreate()
        return render_template("plate-create.html", form=form, searchform = searchform)
    else:

        project = machine.session.query(models.Project).filter_by(owner=current_user, name=request.form['project']).one_or_none()

        name = request.form['name']
        ignore = request.form['ignore'].split(",")
        f = request.files['data']
        data = pd.read_csv(f)

        if 'design' in request.files:
            f = request.files['design']
            meta = pd.read_csv(f)

            if len(ignore) > 0:
                for i in ignore:
                    if i == "":
                        continue
                    del meta[i]
        else:
            meta = None

        if request.form['source'] == 'csv':
            plate = machine.createPlate(project, name, data, meta)
        else:
            flask.flash('only csv source supported currently!')
            pass

        return redirect(url_for('plates'))


@app.route('/designs/')
def designs():
    if current_user.is_authenticated:
        designs = machine.session.query(models.Design).join(models.Project).filter(or_(models.Project.published, models.Project.owner==current_user)).all()
    else:
        designs = machine.session.query(models.Design).join(models.Project).filter(models.Project.published).all()
    searchform = SearchForm()

    return render_template("designs.html", designs=designs, searchform=searchform)

@app.route('/design/<_id>',methods=['GET'])
@app.route('/design/<_id>/<plate>')
def design(_id, plate=None):
    searchform = SearchForm()
    designform = DesignForm()

    design = machine.session.query(models.Design)\
                .filter(models.Design.id==_id).one_or_none()

    designform.type.default = design.type
    designform.process()

    if request.method == 'GET':

        designform.type.default = design.type

        values = machine.session.query(models.ExperimentalDesign)\
                    .join(models.Design)\
                    .filter(models.Design.id==_id)

        wells = machine.session.query(models.Well)\
                    .join(models.well_experimental_design)\
                    .join(models.ExperimentalDesign)\
                    .join(models.Design)\
                    .filter(models.Design.id==_id)

        if not plate is None:
            wells = wells.join(models.Plate).filter(models.Plate.name==plate)

            values = values.join(models.well_experimental_design)\
                        .join(models.Well)\
                        .join(models.Plate).filter(models.Plate.name==plate)

        ds = machine.get(wells, include=[design.name])

        assert not any(ds.meta[design.name].isnull())

        color = map(lambda x: ds.meta[design.name].unique().tolist().index(x), ds.meta[design.name])

        return plotDataset(ds, 'design.html', color=ds.meta[design.name], values=values, design=design,
                searchform=searchform, plate=plate, designform=designform)

    else:
        design.type = request.form['type']
        machine.session.commit()

        return redirect(url_for("design", _id=design.id))

@app.route('/design_edit/<_id>', methods=['GET', 'POST'])
@login_required
def design_edit(_id):

    searchform = SearchForm()

    design = machine.session.query(models.Design)\
                .filter(models.Design.id==_id).one_or_none()

    class DynamicDesignForm(DesignForm):

        description = TextAreaField('description', default=design.description)
        protocol = TextAreaField('protocol', default=design.protocol)

    designform = DynamicDesignForm()

    designform.type.default = design.type
    designform.description.default = design.description
    designform.protocol.default = design.protocol
    designform.process()

    if request.method == 'GET':

        return render_template('design-edit.html', searchform=searchform, designform=designform, design=design)

    else:
        design.type = request.form['type']
        design.description = request.form['description']
        design.protocol = request.form['protocol']
        machine.session.commit()

        return redirect(url_for("design", _id=design.id))


@app.route('/experimentaldesign/<_id>')
@app.route('/experimentaldesign/<_id>/<plate>')
def experimentalDesign(_id, plate=None):
    searchform = SearchForm()

    ed = machine.session.query(models.ExperimentalDesign)\
                .filter(models.ExperimentalDesign.id==_id).one_or_none()

    wells = machine.session.query(models.Well)\
                .join(models.well_experimental_design)\
                .join(models.ExperimentalDesign)\
                .filter(models.ExperimentalDesign.id==_id)

    if not plate is None:
        wells = wells.join(models.Plate).filter(models.Plate.name==plate)

    ds = machine.get(wells, include=[ed.design.name])

    return plotDataset(ds, "experimental-design.html", color=ds.meta[ed.design.name], wells=wells, experimentalDesign=ed, searchform=searchform)
    return render_template("experimental-design.html", wells=wells, experimentalDesign=ed, searchform=searchform)

@app.route('/search/',methods=['GET', 'POST'])
def search():

    searchform = SearchForm()

    if request.method=='GET':
        return render_template("search.html", searchform=searchform)
    else:
        groups = re.findall("(([0-9a-zA-Z -.]+)=([0-9a-zA-Z ,.-]+))", request.form['search'])

        kwargs = {}
        for _, k, v in groups:
            k = k.strip().rstrip()
            v = v.split(",")
            v = [z.strip().rstrip() for z in v]
            kwargs[k] = v

        session['designs'] = [d.id for d in machine.session.query(models.Design).filter(models.Design.name.in_(kwargs.keys()))]
        session['wells'] = [w.id for w in machine.filter(**kwargs)]
        ds = machine.search(**kwargs)

        # print ds.data.head()

        if ds is None:
            flash('No data found for search: %s'%str(kwargs))
            return render_template("dataset.html", searchform=searchform)
        else:
            # color = None
            # # if len(groups)>0:
            # for k, v in kwargs.iteritems():
            #     if str(k) in ['include', 'plates']:
            #         continue
            #     color = map(lambda x: ds.meta[k].unique().tolist().index(x), ds.meta[k])
            #     break

            # return plotDataset(ds, 'dataset.html', searchform=searchform, dataset=ds)
            return plotDataset(ds, 'dataset.html', searchform=searchform)

@app.route('/phenotype/<id>')
def phenotype(id):
    searchform = SearchForm()

    phenotype = machine.session.query(models.Phenotype).filter_by(id=id).one_or_none()

    wells = machine.session.query(models.Well).filter(models.Well.id.in_([w.id for w in phenotype.wells]))
    ds = machine.get(wells, include=[d.name for d in phenotype.designs])

    dsp = design_space.design_space(machine.session, phenotype)

    values = {}
    for d in phenotype.designs:
         q = machine.session.query(models.ExperimentalDesign)\
                    .join(models.well_experimental_design)\
                    .join(models.Well)\
                    .filter(models.ExperimentalDesign.design==d)\
                    .filter(models.Well.id.in_([w.id for w in wells]))

         values[d.name] = q.all()

    return plotDataset(ds, 'phenotype.html', searchform=searchform, phenotype=phenotype, values=values, dsp=dsp)
    # return render_template('phenotype.html', phenotype=phenotype, searchform = searchform)

@app.route('/phenotypes')
def phenotypes():
    searchform = SearchForm()
    if not current_user.is_authenticated:
        phenotypes = machine.session.query(models.Phenotype).join(models.Project).filter(models.Project.published).all()

    else:
        phenotypes = machine.session.query(models.Phenotype).join(models.Project).filter(or_(models.Project.owner==current_user, models.Project.published)).all()

    return render_template('phenotypes.html', phenotypes=phenotypes, searchform=searchform)

@app.route('/phenotype-create', methods=['GET', 'POST'])
@login_required
def phenotype_create():
    searchform = SearchForm()
    phenotype_form = PhenotypeForm()

    if request.method == 'GET':
        return render_template("phenotype-edit.html", searchform=searchform, form=phenotype_form, operation='create')
    else:
        wells = machine.session.query(models.Well).filter(models.Well.id.in_(session.pop('wells', None))).all()
        designs = machine.session.query(models.Design).filter(models.Design.id.in_(session.pop('designs', None))).all()
        name = request.form['name']

        project = wells[0].plate.project

        phenotype = models.Phenotype(name=name, owner=current_user, wells=wells, designs=designs, project=project)
        machine.session.add(phenotype)
        machine.session.commit()

        return redirect(url_for('phenotype', id=phenotype.id))


@app.route('/login', methods=['GET', 'POST'])
def login():

    searchform = SearchForm()
    # Here we use a class of some kind to represent and validate our
    # client-side form data. For example, WTForms is a library that will
    # handle this for us, and we use a custom LoginForm to validate.
    form = LoginForm()
    if form.validate_on_submit():

        user = machine.session.query(models.User).filter_by(username=request.form['name']).one_or_none()

        if user is None or not user.is_correct_password(str(request.form['password'])):
            flask.flash('Incorrect username or password.')
            return flask.redirect(flask.url_for('login', form=form, method='GET'))

        login_user(user)

        flask.flash('Logged in successfully.')

        next = flask.request.args.get('next')
        if not is_safe_url(next):
            return flask.abort(400)

        return flask.redirect(next or flask.url_for('index'))
    return flask.render_template('login.html', form=form, searchform=searchform)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@login_manager.unauthorized_handler
def unauthorized():
    # do stuff
    flask.flash('you must be logged in to do that!')
    return redirect(flask.url_for('login'))
