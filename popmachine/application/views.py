from app import app
from flask import Flask, render_template, request, jsonify
from popmachine import Machine, models
from .forms import SearchForm
import re

machine = Machine()

@app.route('/')
def index():
    plates = machine.plates()
    searchform = SearchForm()

    return render_template("index.html", plates=plates, searchform=searchform)

@app.route('/hello')
def hello():
    return 'Hello, World'

@app.route('/plates/')
def plates():
    plates = machine.plates()
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

    return render_template("plate.html", plate=plate, experimentalDesigns=experimentalDesigns, searchform = searchform)

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

        ds = machine.search(**kwargs)

        from bokeh.embed import components
        from bokeh.plotting import figure
        from bokeh.resources import INLINE
        from bokeh.util.string import encode_utf8

        fig = figure(title="Dataset")
        fig.line(ds.data.index.values, ds.data.values[:,0], line_width=2)
        # fig.line(range(10), range(10))

        js_resources = INLINE.render_js()
        css_resources = INLINE.render_css()
        script, div = components(fig)

        html = render_template(
            'dataset.html',
            plot_script=script,
            plot_div=div,
            js_resources=js_resources,
            css_resources=css_resources,
            searchform=searchform
        )
        return encode_utf8(html)

        return render_template("dataset.html", searchform=searchform, dataset=ds )

        return str(groups)

        return str(request.form)
        # all_args = request.args.lists()
        # return jsonify(all_args)
