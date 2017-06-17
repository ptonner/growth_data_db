from ..forms import SearchForm
from ..plot import plotDataset
from popmachine.models import Project, Model, Phenotype, Covariate, Test

import datetime
from sqlalchemy import not_, or_
import flask
from flask import Blueprint, current_app, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import SelectField, SelectMultipleField
from wtforms.validators import DataRequired

profile = Blueprint('model', __name__)


@profile.route('/model/<id>')
def model(id):
    if current_user.is_authenticated:
        model = current_app.machine.session.query(Model)\
            .filter_by(id=id)\
            .join(Phenotype)\
            .join(Project)\
            .filter(or_(Project.published, Project.owner == current_user)).one_or_none()
    else:
        model = current_app.machine.session.query(Model)\
            .filter_by(id=id)\
            .join(Phenotype)\
            .join(Project)\
            .filter(Project.published).one_or_none()

    if model is None:
        flask.flash('no model found or insufficient permissions!')
        flask.redirect(url_for('misc.index'))

    searchform = SearchForm()
    return render_template("model/model.html", model=model, searchform=searchform)


@profile.route('/model/create/<id>', methods=['GEt', 'POST'])
@login_required
def create(id):

    phenotype = current_app.machine.session.query(Phenotype).filter_by(
        id=id, owner=current_user).one_or_none()

    choices = [(d.name, d.name) for d in phenotype.designs]

    for i in range(len(phenotype.designs)):
        for j in range(i + 1, len(phenotype.designs)):

            d1, d2 = phenotype.designs[i], phenotype.designs[j]
            s = '%s:%s' % (d1.name, d2.name)
            choices.append((s, s))

    class ModelForm(FlaskForm):
        covariates = SelectMultipleField(
            'covariates', choices=choices)

    searchform = SearchForm()
    form = ModelForm()

    if form.validate_on_submit():

        if form.covariates.data:
            covariates = [Covariate(
                designs=[d]) for d in phenotype.designs if d.name in form.covariates.data]

            for c in form.covariates.data:
                if ':' in c:
                    designs = c.split(":")
                    covariates.append(
                        Covariate(designs=[d for d in phenotype.designs if d.name in designs]))
        else:
            covariates = []

        now = datetime.datetime.now()
        model = Model(phenotype=phenotype, covariates=covariates,
                      queue_time=now, status='queued')
        current_app.machine.session.add(model)
        current_app.machine.session.commit()

        return redirect(url_for('model.queue'))

    if not phenotype:
        flask.flash('no phenotype found or incorrect permissions!')
        return flask.redirect(url_for('misc.index'))

    return render_template('model/create.html', phenotype=phenotype, form=form, searchform=searchform)


@profile.route('/model/queue')
@login_required
def queue():
    searchform = SearchForm()
    models = current_app.machine.session.query(Model).filter_by(
        status='queued').order_by(Model.queue_time).all()

    return render_template('model/queue.html', models=models, searchform=searchform)


@profile.route('/model/<id>/delete', methods=['GET', 'POST'])
@login_required
def delete(id):
    searchform = SearchForm()
    model = current_app.machine.session.query(
        Model).filter_by(id=id).one_or_none()
    phenotype = model.phenotype

    if not model:
        flask.flash('no model found!')
        return flask.redirect(url_for('misc.index'))

    if request.method == 'GET':
        return render_template('delete.html', searchform=searchform, name='Model %d' % model.id, url=url_for('model.delete', id=model.id))
    else:
        current_app.machine.session.delete(model)
        current_app.machine.session.commit()
        flask.flash('model deleted!')
        return flask.redirect(url_for('phenotype', id=phenotype.id))


@profile.route('/covariate/<id>')
def covariate(id):
    searchform = SearchForm()
    covariate = current_app.machine.session.query(
        Covariate).filter_by(id=id).one_or_none()

    if not covariate:
        flask.flash('no covariate found!')
        return flask.redirect(url_for('misc.index'))

    return render_template('model/covariate.html', searchform=searchform, covariate=covariate)


@profile.route('/test/create/<id>', methods=['GET', 'POST'])
@login_required
def create_test(id):

    phenotype = current_app.machine.session.query(Phenotype).filter_by(
        id=id, owner=current_user).one_or_none()

    if not phenotype:
        flask.flash('no phenotype found or incorrect permissions!')
        return flask.redirect(url_for('misc.index'))

    models = [(m.id, m.name) for m in phenotype.models]

    class TestForm(FlaskForm):
        alternative_model = SelectField(
            'alternative_model', choices=models, validators=[DataRequired()], coerce=int)
        null_model = SelectField(
            'null_model', choices=models, validators=[DataRequired()], coerce=int)

    searchform = SearchForm()
    form = TestForm()

    if form.validate_on_submit():

        am = current_app.machine.session.query(Model).filter_by(
            id=form.alternative_model.data).one_or_none()
        nm = current_app.machine.session.query(Model).filter_by(
            id=form.null_model.data).one_or_none()

        test = Test(alternative_model=am, null_model=nm, phenotype=phenotype)
        current_app.machine.session.add(test)
        current_app.machine.session.commit()

        return redirect(url_for('phenotype', id=phenotype.id))

    elif request.method == 'POST':
        flask.flash('form validation failed!')

    return render_template('model/test-create.html', phenotype=phenotype, form=form, searchform=searchform)


@profile.route('/test/<id>/delete', methods=['GET', 'POST'])
@login_required
def delete_test(id):
    searchform = SearchForm()
    test = current_app.machine.session.query(
        Test).filter_by(id=id).one_or_none()
    phenotype = test.phenotype

    if not model:
        flask.flash('no test found!')
        return flask.redirect(url_for('misc.index'))

    if request.method == 'GET':
        return render_template('delete.html', searchform=searchform, name='Test %d' % test.id, url=url_for('model.delete_test', id=test.id))
    else:
        current_app.machine.session.delete(test)
        current_app.machine.session.commit()
        flask.flash('test deleted!')
        return flask.redirect(url_for('phenotype', id=phenotype.id))
