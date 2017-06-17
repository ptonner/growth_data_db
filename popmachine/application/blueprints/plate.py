from ..forms import SearchForm, PlateCreate
from popmachine import models

from sqlalchemy import not_, or_
import flask
from flask import Blueprint, current_app, render_template, redirect, url_for, request
from flask_login import login_required, current_user

profile = Blueprint('plate', __name__)


@profile.route('/plates/')
def plates():

    if current_user.is_authenticated:
        plates = current_app.machine.session.query(models.Plate).join(models.Project).filter(
            or_(models.Project.published, models.Project.owner == current_user)).all()
    else:
        plates = current_app.machine.session.query(models.Plate).join(
            models.Project).filter(models.Project.published).all()

    searchform = SearchForm()

    return render_template("plates.html", plates=plates, searchform=searchform)


@profile.route('/plate/<platename>')
def plate(platename):
    searchform = SearchForm()
    plate = current_app.machine.session.query(models.Plate).filter(
        models.Plate.name == platename).one_or_none()

    experimentalDesigns = current_app.machine.session.query(models.ExperimentalDesign)\
        .join(models.well_experimental_design)\
        .join(models.Well)\
        .filter(models.Well.id.in_([w.id for w in plate.wells]))

    designs = current_app.machine.session.query(models.Design)\
        .join(models.ExperimentalDesign)\
        .join(models.well_experimental_design)\
        .join(models.Well)\
        .filter(models.Well.id.in_([w.id for w in plate.wells]))

    return render_template("plate.html", plate=plate, experimentalDesigns=experimentalDesigns, designs=designs, searchform=searchform)


@profile.route('/plate-delete/<platename>', methods=['GET', 'POST'])
def plate_delete(platename):
    searchform = SearchForm()

    if request.method == 'GET':
        return render_template('plate-delete.html', searchform=searchform, platename=platename)
    else:
        plate = current_app.machine.session.query(models.Plate).filter(
            models.Plate.name == platename).one_or_none()
        current_app.machine.deletePlate(plate.project, plate)

        return redirect(url_for('plate.plates'))


@profile.route('/plate-create/', methods=['GET', "POST"])
@login_required
def plate_create():

    searchform = SearchForm()

    myprojects = current_app.machine.session.query(
        models.Project).filter_by(owner=current_user).all()

    class DynamicPlateCreate(PlateCreate):
        project = SelectField("project", choices=[
                              (p.name, p.name) for p in myprojects])

    if request.method == "GET":
        form = DynamicPlateCreate()
        return render_template("plate-create.html", form=form, searchform=searchform)
    else:

        project = current_app.machine.session.query(models.Project).filter_by(
            owner=current_user, name=request.form['project']).one_or_none()

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
            plate = current_app.machine.createPlate(project, name, data, meta)
        else:
            flask.flash('only csv source supported currently!')
            pass

        return redirect(url_for(plates))
