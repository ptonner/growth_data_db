from ..forms import SearchForm
from ..plot import plotDataset
from .. import machine
from popmachine.models import Project, Model, Phenotype

import datetime
from sqlalchemy import not_, or_
import flask
from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import SelectMultipleField

profile = Blueprint('model', __name__)


@profile.route('/model/<id>')
def model(id):
    if current_user.is_authenticated:
        model = machine.session.query(Model)\
            .filter_by(id=id)\
            .join(Phenotype)\
            .join(Project)\
            .filter(or_(Project.published, Project.owner == current_user)).one_or_none()
    else:
        model = machine.session.query(Model)\
            .filter_by(id=id)\
            .join(Phenotype)\
            .join(Project)\
            .filter(Project.published).one_or_none()

    if model is None:
        flask.flash('no model found or insufficient permissions!')
        flask.redirect(url_for('index'))

    searchform = SearchForm()
    return render_template("model/model.html", model=model, searchform=searchform)


@profile.route('/model/create/<id>', methods=['GEt', 'POST'])
@login_required
def create(id):

    phenotype = machine.session.query(Phenotype).filter_by(
        id=id, owner=current_user).one_or_none()

    class ModelForm(FlaskForm):
        covariates = SelectMultipleField(
            'covariates', choices=[(d.name, d.name) for d in phenotype.designs])

    searchform = SearchForm()
    form = ModelForm()

    if form.validate_on_submit():

        now = datetime.datetime.now()
        model = Model(phenotype=phenotype, covariates=[
                      d for d in phenotype.designs if d.name in form.covariates.data],
                      queue_time=now, status='queued')
        machine.session.add(model)
        machine.session.commit()

        return redirect(url_for('model.queue'))

    if not phenotype:
        flask.flash('no phenotype found or incorrect permissions!')
        return flask.redirect(url_for('index'))

    return render_template('model/create.html', phenotype=phenotype, form=form, searchform=searchform)


@profile.route('/model/queue')
@login_required
def queue():
    searchform = SearchForm()
    models = machine.session.query(Model).filter_by(
        status='queued').order_by(Model.queue_time).all()

    return render_template('model/queue.html', models=models, searchform=searchform)


@profile.route('/model/<id>/delete', methods=['GET', 'POST'])
@login_required
def delete(id):
    searchform = SearchForm()
    model = machine.session.query(Model).filter_by(id=id).one_or_none()

    if not model:
        flask.flash('no model found!')
        return flask.redirect(url_for('index'))

    if request.method == 'GET':
        return render_template('delete.html', searchform=searchform, name='Model %d' % model.id, url=url_for('model.delete', id=model.id))
    else:
        machine.session.delete(model)
        flask.flash('model deleted!')
        return flask.redirect(url_for('index'))
