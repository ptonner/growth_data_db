from flask import render_template

import numpy as np

from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.charts import TimeSeries
from bokeh.resources import INLINE
from bokeh.util.string import encode_utf8
from bokeh.palettes import Spectral11, viridis
from bokeh.io import output_file, show, vform
from bokeh.layouts import widgetbox
from bokeh.models import CustomJS, ColumnDataSource, Plot
from bokeh.models.widgets import Dropdown
from bokeh.models.glyphs import MultiLine
from bokeh.layouts import column, row

def colorby(values):

    if not values.dtype == int:
        values = [values.unique().tolist().index(v) for v in values]

    v = viridis(max(values)+1)
    color = [v[c] for c in values]

    return color

def plotDataset(ds,template='dataset.html',title='Dataset',color=None,*args, **kwargs):

    ds = ds.copy()
    ds.data.columns = ds.data.columns.astype(str)


    # ts = TimeSeries(ds.data)

    numlines=len(ds.data.columns)

    if color is None:
        color = ds.meta[ds.meta.columns[0]]
    label = color
    color = colorby(color)

    # print color

    # source = ColumnDataSource(data=ds.data)
    # source = ColumnDataSource(dict(xs=[ds.data.index.values]*ds.data.shape[1],
    #             ys = [ds.data[name].values for name in ds.data], yslog = [np.log2(ds.data[name].values) for name in ds.data], color=color, label=label))
    source = ColumnDataSource(dict(xs=[ds.data.index.values]*ds.data.shape[1],
                ys = [ds.data[name].values for name in ds.data], color=color, label=label))

    labelsource = ColumnDataSource(ds.meta)
    colorsource = ColumnDataSource({k:colorby(ds.meta[k]) for k in ds.meta.columns.tolist()})


    # if color is None:
    #     # color = viridis(numlines)
    #     color = colorby(range(numlines))
    # else:
    #     # v = viridis(max(color)+1)
    #     # color = [v[c] for c in color]
    #     color = colorby(color)

    fig = figure(title=title,plot_width=97*8,)
    # plot = Plot()
    # fig.line(ds.data.index.values, ds.data, line_width=2)

    # fig.multi_line(xs=[ds.data.index.values]*ds.data.shape[1],
    #             ys = [ds.data[name].values for name in ds.data],
    #             line_color=color,
    #             line_width=5)
    fig.multi_line('xs', 'ys', color='color', legend='label', source=source)

    fig.legend.location = "top_left"

    # glyph = MultiLine(xs="xs", ys="ys", line_color="", line_width=2)
    # fig.add_glyph(source, glyph)
    # plot.add_glyph(source, glyph)

    callback = CustomJS(args=dict(source=source,colorsource=colorsource,labelsource=labelsource), code="""
        var data = source.get('data');
        var data2 = colorsource.get('data');
        var data3 = labelsource.get('data');
        var f = cb_obj.get('value')

        color = data['color']
        color2 = data2[f]

        label = data['label']
        label2 = data3[f]

        for (i = 0; i < color.length; i++) {
            color[i] = color2[i]
            label[i] = label2[i]
        }

        source.trigger('change');
    """)

    # logcallback = CustomJS(args=dict(source=source), code="""
    #     var data = source.get('data');
    #
    #     data['ys'] = data['yslog']
    #
    #     source.trigger('change');
    # """)

    menu = [(c,c) for c in ds.meta.columns]
    dropdown = Dropdown(label="Color by", button_type="warning", menu=menu, callback=callback)

    # layout = vform(dropdown, fig)
    layout = column(dropdown, fig)

    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()

    # script, div = components(ts)
    script, div = components(layout)
    # script, div = components(fig)

    html = render_template(
        template,
        plot_script=script,
        plot_div=div,
        js_resources=js_resources,
        css_resources=css_resources,
        *args, **kwargs
    )
    return encode_utf8(html)
