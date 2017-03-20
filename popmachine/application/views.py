from app import app
from flask import Flask, render_template, request, jsonify
from popmachine import Machine, models
from .forms import SearchForm
import re

machine = Machine()

@app.route('/')
def index():
    plates = machine.plates()
    form = SearchForm()

    return render_template("index.html", plates=plates, form=form)

@app.route('/hello')
def hello():
    return 'Hello, World'

@app.route('/plates/')
def plates():
    plates = machine.plates()
    return render_template("plates.html", plates=plates)

@app.route('/plate/<platename>')
def plate(platename):
    plate = machine.session.query(models.Plate).filter(models.Plate.name==platename).one_or_none()

    experimentalDesigns = machine.session.query(models.ExperimentalDesign)\
                .join(models.well_experimental_design)\
                .join(models.Well)\
                .filter(models.Well.id.in_([w.id for w in plate.wells]))

    return render_template("plate.html", plate=plate, experimentalDesigns=experimentalDesigns)

@app.route('/experimentaldesign/<_id>')
@app.route('/experimentaldesign/<_id>/<plate>')
def experimentalDesign(_id, plate=None):
    ed = machine.session.query(models.ExperimentalDesign)\
                .filter(models.ExperimentalDesign.id==_id).one_or_none()

    wells = machine.session.query(models.Well)\
                .join(models.well_experimental_design)\
                .join(models.ExperimentalDesign)\
                .filter(models.ExperimentalDesign.id==_id)

    if not plate is None:
        wells = wells.join(models.Plate).filter(models.Plate.name==plate)

    return render_template("experimental-design.html", wells=wells, experimentalDesign=ed)

@app.route('/search/',methods=['GET', 'POST'])
def search():

    if request.method=='GET':
        from .forms import SearchForm
        form = SearchForm()

        return render_template("search.html", form=form)
    else:
        groups = re.findall("(([0-9a-zA-Z ]+)=([0-9a-zA-Z ,.]+))", request.form['search'])
        return str(groups)

        return str(request.form)
        # all_args = request.args.lists()
        # return jsonify(all_args)
