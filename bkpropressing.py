import pysal as ps
import numpy as np
import geopandas as gpd
import pandas as pd
import shapely as shp
from shapely.geometry import shape
import json
from bokeh.models import (
    ColumnDataSource,
    HoverTool,
    LogColorMapper
)
from bokeh.io import output_file, show
from bokeh.models import GeoJSONDataSource,CategoricalColorMapper
from bokeh.plotting import figure
from bokeh.sampledata.sample_geojson import geojson
from bokeh.resources import CDN
from bokeh.embed import file_html
from bokeh.charts.attributes import cat, color

def gpd_bokeh(df):
    """Convert geometries from geopandas to bokeh format"""
    nan = float('nan')
    lons = []
    lats = []
    for i,shape in enumerate(df.geometry.values):
        if shape.geom_type == 'MultiPolygon':
            print 'MultiPolygon'
            gx = []
            gy = []
            ng = len(shape.geoms) - 1
            for j,member in enumerate(shape.geoms):
                xy = np.array(list(member.exterior.coords))
                xs = xy[:,0].tolist()
                ys = xy[:,1].tolist()
                gx.extend(xs)
                gy.extend(ys)
                if j < ng:
                    gx.append(nan)
                    gy.append(nan)
            lons.append(gx)
            lats.append(gy)

        else:
            print 'else'
            xy = np.array(list(shape.exterior.coords))
            xs = xy[:,0].tolist()
            ys = xy[:,1].tolist()
            lons.append(xs)
            lats.append(ys)

    return lons,lats

def bkExport(settings):
#layer = iface.legendInterface().layers()[0]
    layer = settings["layer"]
    field = settings["field"]
    gdfList = []
    for feature in layer.getFeatures():
        #print feature.geometry().exportToGeoJSON(17)
        print "feature"
        featJsonString = feature.geometry().geometry().asJSON(17)
        featJson = json.loads(featJsonString)
        df = {}
        df["geometry"] = shape(featJson)
        df["data"] = feature[field]
        df["class"] = -1
        gdf = gpd.GeoDataFrame([df])
        gdfList.append(gdf)

    gdf2 = gpd.GeoDataFrame(pd.concat(gdfList,ignore_index=True))
    print len(gdfList)
    print gdf2

    lons, lats = gpd_bokeh(gdf2)
    data = list(gdf2["data"])

    #map settings
    #width = int(layer.extent().width()*20)
    #height = int(layer.extent().height()*20)
    width = 1000
    height = 600
    renderer = layer.rendererV2()
    if renderer.type() == 'singleSymbol':
        print "singleSymbol"
        color = renderer.symbol().color().name()
        color_mapper = CategoricalColorMapper(factors=[-1], palette=[color])
    elif renderer.type() == 'categorizedSymbol':
        print "categorizedSymbol"

    elif renderer.type() == 'graduatedSymbol':
        print "graduatedSymbol"
        ranges = renderer.ranges()

        for i in xrange(len(ranges)):
            print ranges[i].lowerValue()
            print ranges[i].upperValue()
            gdf2["class"][(gdf2["data"] >= ranges[i].lowerValue()) & (gdf2["data"] <= ranges[i].upperValue())] = i

        print gdf2["class"]
        colorPalette = [symbol.color().name() for symbol in renderer.symbols()]
        color_mapper = CategoricalColorMapper(factors=sorted(list(gdf2["class"].unique())), palette=colorPalette)
        print sorted(list(gdf2["class"].unique())),colorPalette
        print color_mapper
    else:
        print "otherSymbols"
    TOOLS = "pan,wheel_zoom,box_zoom,reset,hover,save"

    colorClass  = list(gdf2["class"])
    source = ColumnDataSource(data=dict(
        x=lons,
        y=lats,
        data = data,
        category = colorClass
    ))
    #plot_width=width, plot_height=height,
    p = figure(
        title="Texas Unemployment, 2009", tools=TOOLS,plot_width=width, plot_height=height,
        x_axis_location=None, y_axis_location=None
    )
    p.grid.grid_line_color = None
    p.patches('x', 'y', source=source, fill_alpha=0.7, line_color="black", line_width=0.5,fill_color = {'field': 'category', 'transform': color_mapper},)


    hover = p.select_one(HoverTool)
    hover.point_policy = "follow_mouse"
    hover.tooltips = [
        (field, "@data")
        #("(Long, Lat)", "($x, $y)"),
    ]


    html = file_html(p, CDN, "my plot")

    with open(settings["outputFile"], "w") as my_file:
        my_file.write(html)
    print ("exported")
