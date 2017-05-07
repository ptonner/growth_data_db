from ..forms import SearchForm, DesignForm
from ..plot import plotDataset
from .. import machine
from popmachine import models

from sqlalchemy import not_, or_
import flask
from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from wtforms import TextAreaField

profile = Blueprint('design', __name__)

@profile.route('/designs/')
def designs():
    if current_user.is_authenticated:
        designs = machine.session.query(models.Design).join(models.Project).filter(or_(models.Project.published, models.Project.owner==current_user)).all()
    else:
        designs = machine.session.query(models.Design).join(models.Project).filter(models.Project.published).all()
    searchform = SearchForm()

    return render_template("designs.html", designs=designs, searchform=searchform)

@profile.route('/design/<_id>',methods=['GET'])
@profile.route('/design/<_id>/<plate>')
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

        return redirect(url_for('design.design', _id=design.id))

@profile.route('/design_edit/<_id>', methods=['GET', 'POST'])
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

        return redirect(url_for('design.design', _id=design.id))
