from app import app
from flask import Flask, render_template, request, jsonify
from popmachine import Machine, models
from .forms import SearchForm
import re

from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.charts import TimeSeries
from bokeh.resources import INLINE
from bokeh.util.string import encode_utf8

machine = Machine()

def datasetHtml(ds,template,title='Dataset',*args, **kwargs):

    ds = ds.copy()
    ds.data.columns = ds.data.columns.astype(str)

    ts = TimeSeries(ds.data)

    fig = figure(title=title)
    fig.line(ds.data.index.values, ds.data, line_width=2)

    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()

    script, div = components(ts)

    html = render_template(
        template,
        plot_script=script,
        plot_div=div,
        js_resources=js_resources,
        css_resources=css_resources,
        *args, **kwargs
    )
    return encode_utf8(html)

@app.route('/')
def index():
    plates = machine.plates()
    searchform = SearchForm()

    return render_template("index.html", plates=plates, searchform=searchform)

@app.route('/plates/')
def plates():
    plates = machine.plates()
    searchform = SearchForm()

    return render_template("plates.html", plates=plates, searchform=searchform)


@app.route('/designs/')
def designs():
    designs = machine.designs()
    searchform = SearchForm()

    return render_template("designs.html", designs=designs, searchform=searchform)


@app.route('/plate/<platename>')
def plate(platename):
    searchform = SearchForm()
    plate = machine.session.query(models.Plate).filter(models.Plate.name==platename).one_or_none()

    experimentalDesigns = machine.session.query(models.ExperimentalDesign)\
                .join(models.well_experimental_design)\
                .join(models.Well)\
                .filter(models.Well.id.in_([w.id for w in plate.wells]))

    return render_template("plate.html", plate=plate, experimentalDesigns=experimentalDesigns, searchform = searchform)

@app.route('/design/<_id>')
@app.route('/design/<_id>/<plate>')
def design(_id, plate=None):
    searchform = SearchForm()

    design = machine.session.query(models.Design)\
                .filter(models.Design.id==_id).one_or_none()

    values = machine.session.query(models.ExperimentalDesign)\
                .join(models.Design)\
                .filter(models.Design.id==_id)

    wells = machine.session.query(models.Well)\
                .join(models.well_experimental_design)\
                .join(models.ExperimentalDesign)\
                .join(models.Design)\
                .filter(models.Design.id==_id)

    ds = machine.get(wells, include=[design.name])
    # ds.data.columns = ds.meta[design.name]

    assert not any(ds.meta[design.name].isnull())

    if not plate is None:
        # wells = wells.join(models.Plate).filter(models.Plate.name==plate)

        values = values.join(models.well_experimental_design)\
                    .join(models.Well)\
                    .join(models.Plate).filter(models.Plate.name==plate)
    # else:
    #     plate = ""

    return datasetHtml(ds, 'design.html', values=values, design=design, searchform=searchform, plate=plate)
    # return render_template("design.html", wells=wells, design=design, searchform=searchform)

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

    return render_template("experimental-design.html", wells=wells, experimentalDesign=ed, searchform=searchform)

@app.route('/search/',methods=['GET', 'POST'])
def search():

    searchform = SearchForm()

    if request.method=='GET':
        return render_template("search.html", searchform=searchform)
    else:
        groups = re.findall("(([0-9a-zA-Z ]+)=([0-9a-zA-Z ,.]+))", request.form['search'])

        kwargs = {}
        for _, k, v in groups:
            k = k.strip().rstrip()
            v = v.split(",")
            v = [z.strip().rstrip() for z in v]
            kwargs[k] = v

        wells = machine.filter(**kwargs)

        ds = machine.search(**kwargs)

        return datasetHtml(ds, 'dataset.html',searchform=searchform, dataset=ds)
