"""
Holding ground for unsorted urls, this should be empty soon!
"""


# from . import machine
from popmachine import models
from popmachine.phenotype import design_space
from ..app import login_manager
from ..forms import SearchForm, DesignForm, PhenotypeForm
from ..plot import plotDataset
from ..safeurl import is_safe_url

import re
import flask
import datetime
import pandas as pd
from flask import Blueprint, current_app, render_template, request, jsonify, url_for, redirect, flash, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

from sqlalchemy import or_, not_
from wtforms import SelectField, StringField, TextAreaField

from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.charts import TimeSeries
from bokeh.resources import INLINE
from bokeh.util.string import encode_utf8
from bokeh.palettes import Spectral11, viridis

profile = Blueprint('misc', __name__)


@login_manager.user_loader
def load_user(user_id):
    return current_app.machine.session.query(models.User).filter_by(id=user_id).one_or_none()


@profile.route('/')
def index():

    if not current_user.is_authenticated:
        projects = current_app.machine.session.query(
            models.Project).filter_by(published=True).all()
        plates = current_app.machine.session.query(models.Plate).join(
            models.Project).filter(models.Project.published).all()
        designs = current_app.machine.session.query(models.Design).join(
            models.Project).filter(models.Project.published).all()

        phenotypes = current_app.machine.session.query(models.Phenotype).join(
            models.Project).filter(models.Project.published).all()

    else:
        projects = current_app.machine.session.query(models.Project).filter(
            or_(models.Project.owner == current_user, models.Project.published)).all()
        plates = current_app.machine.session.query(models.Plate).join(
            models.Project).filter(models.Project.owner == current_user).all()
        designs = current_app.machine.session.query(models.Design).join(models.Project).filter(
            or_(models.Project.owner == current_user, models.Project.published)).all()

        phenotypes = current_app.machine.session.query(models.Phenotype).join(models.Project).filter(
            or_(models.Project.owner == current_user, models.Project.published)).all()

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


@profile.route('/bgreat/')
def bgreat():
    print 'bgreat'
    searchform = SearchForm()
    return render_template("bgreat.html", searchform=searchform)


@profile.route('/experimentaldesign/<_id>')
@profile.route('/experimentaldesign/<_id>/<plate>')
def experimentalDesign(_id, plate=None):
    searchform = SearchForm()

    ed = current_app.machine.session.query(models.ExperimentalDesign)\
        .filter(models.ExperimentalDesign.id == _id).one_or_none()

    wells = current_app.machine.session.query(models.Well)\
        .join(models.well_experimental_design)\
        .join(models.ExperimentalDesign)\
        .filter(models.ExperimentalDesign.id == _id)

    if not plate is None:
        wells = wells.join(models.Plate).filter(models.Plate.name == plate)

    ds = current_app.machine.get(wells, include=[ed.design.name])
    ds.floor()

    return plotDataset(ds, "experimental-design.html", color=ds.meta[ed.design.name], wells=wells, experimentalDesign=ed, searchform=searchform)
    return render_template("experimental-design.html", wells=wells, experimentalDesign=ed, searchform=searchform)


@profile.route('/search', methods=['GET', 'POST'])
def search():

    searchform = SearchForm()

    if request.method == 'GET':
        return render_template("search.html", searchform=searchform)
    else:
        groups = re.findall(
            "(([0-9a-zA-Z ._()-]+)=([0-9a-zA-Z ,.()-]+))", request.form['search'])

        print groups

        kwargs = {}
        for _, k, v in groups:
            k = k.strip().rstrip()
            v = v.split(",")
            v = [z.strip().rstrip() for z in v]
            kwargs[k] = v

        print kwargs

        wells = current_app.machine.filter(**kwargs)

        ds = None
        if wells.count() == 0:
            flash('No data found for search: %s' % str(kwargs))
            return render_template("dataset.html", searchform=searchform)
        elif len(wells.all())>1000:
            flash('Too many wells in search, selecting first 1000')
            wells = wells.limit(1000)
            wells = wells.from_self()
        #     session['designs'] = [d.id for d in current_app.machine.session.query(
        #         models.Design).filter(models.Design.name.in_(kwargs.keys()))]
        #     session['wells'] = [w.id for w in current_app.machine.filter(**kwargs)]
        #     ds = current_app.machine.search(**kwargs)
        #     return plotDataset(ds, 'dataset.html', searchform=searchform)
        # else:
        #     flash('Too many wells in search, selecting first 1000')
        #     wells = wells[:1000]
        #     return render_template("dataset.html", searchform=searchform)

        session['designs'] = [d.id for d in current_app.machine.session.query(
            models.Design).filter(models.Design.name.in_(kwargs.keys()))]
        session['wells'] = [w.id for w in current_app.machine.filter(**kwargs)]

        # ds = current_app.machine.search(**kwargs)
        # ds = current_app.machine.get(wells, include=kwargs.keys())
        ds = current_app.machine._get_intermediate(wells, **kwargs)
        ds.floor()

        return plotDataset(ds, 'dataset.html', searchform=searchform)

        # return plotDataset(ds, 'dataset.html', searchform=searchform)
        #
        # # print ds.data.head()
        #
        # if ds is None:
        #     flash('No data found for search: %s' % str(kwargs))
        #     return render_template("dataset.html", searchform=searchform)
        # else:
        #     # color = None
        #     # # if len(groups)>0:
        #     # for k, v in kwargs.iteritems():
        #     #     if str(k) in ['include', 'plates']:
        #     #         continue
        #     #     color = map(lambda x: ds.meta[k].unique().tolist().index(x), ds.meta[k])
        #     #     break
        #
        #     # return plotDataset(ds, 'dataset.html', searchform=searchform,
        #     # dataset=ds)
        #     return plotDataset(ds, 'dataset.html', searchform=searchform)


@profile.route('/phenotype/<id>')
def phenotype(id):
    searchform = SearchForm()

    phenotype = current_app.machine.session.query(
        models.Phenotype).filter_by(id=id)
    if not current_user.is_authenticated:
        phenotype = phenotype.join(models.Project).filter(
            models.Project.published)
    else:
        phenotype = phenotype.join(models.Project).filter(
            or_(models.Project.owner == current_user, models.Project.published))
    phenotype = phenotype.one_or_none()

    if not phenotype:
        flask.flash('no phenotype found or incorrect permissions!')
        return flask.redirect(url_for('misc.phenotypes'))

    wells = current_app.machine.session.query(models.Well).filter(
        models.Well.id.in_([w.id for w in phenotype.wells]))
    ds = current_app.machine.get(
        wells, include=[d.name for d in phenotype.designs])

    dsp = design_space.design_space(current_app.machine.session, phenotype)

    values = {}
    for d in phenotype.designs:
        q = current_app.machine.session.query(models.ExperimentalDesign)\
            .join(models.well_experimental_design)\
            .join(models.Well)\
            .filter(models.ExperimentalDesign.design == d)\
            .filter(models.Well.id.in_([w.id for w in wells]))

        values[d.name] = q.all()

    return plotDataset(ds, 'phenotype.html', searchform=searchform, phenotype=phenotype, values=values, dsp=dsp, dataSet=ds)


@profile.route('/phenotypes')
def phenotypes():
    searchform = SearchForm()
    if not current_user.is_authenticated:
        phenotypes = current_app.machine.session.query(models.Phenotype).join(
            models.Project).filter(models.Project.published).all()

    else:
        phenotypes = current_app.machine.session.query(models.Phenotype).join(models.Project).filter(
            or_(models.Project.owner == current_user, models.Project.published)).all()

    return render_template('phenotypes.html', phenotypes=phenotypes, searchform=searchform)


@profile.route('/phenotype-create', methods=['GET', 'POST'])
@login_required
def phenotype_create():
    searchform = SearchForm()
    phenotype_form = PhenotypeForm()

    if request.method == 'GET':
        return render_template("phenotype-edit.html", searchform=searchform, form=phenotype_form, operation='create')
    else:
        wells = current_app.machine.session.query(models.Well).filter(
            models.Well.id.in_(session.pop('wells', None))).all()
        designs = current_app.machine.session.query(models.Design).filter(
            models.Design.id.in_(session.pop('designs', None))).all()
        name = request.form['name']

        project = wells[0].plate.project

        phenotype = models.Phenotype(
            name=name, owner=current_user, wells=wells, designs=designs, project=project)
        phenotype.download_phenotype()

        current_app.machine.session.add(phenotype)
        current_app.machine.session.commit()

        return redirect(url_for('phenotype', id=phenotype.id))


@login_manager.unauthorized_handler
def unauthorized():
    # do stuff
    flask.flash('you must be logged in to do that!')
    return redirect(flask.url_for('misc.login'))
