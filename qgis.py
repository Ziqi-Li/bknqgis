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
from bokeh.models import GeoJSONDataSource
from bokeh.plotting import figure
from bokeh.sampledata.sample_geojson import geojson
from bokeh.resources import CDN
from bokeh.embed import file_html

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

def bkExport(layer):
#layer = iface.legendInterface().layers()[0]
    gdfList = []
    for feature in layer.getFeatures():
        #print feature.geometry().exportToGeoJSON(17)
        print "feature"
        featJsonString = feature.geometry().geometry().asJSON(17)
        featJson = json.loads(featJsonString)
        df = {}
        df["geometry"] = shape(featJson)
        gdf = gpd.GeoDataFrame([df])
        gdfList.append(gdf)

    gdf2 = gpd.GeoDataFrame(pd.concat(gdfList,ignore_index=True))
    print len(gdfList)
    print gdf2

    lons, lats = gpd_bokeh(gdf2)
    source = ColumnDataSource(data=dict(
        x=lons,
        y=lats
    ))

    TOOLS = "pan,wheel_zoom,box_zoom,reset,hover,save"
    p = figure(plot_width=600, plot_height=500,
        title="Texas Unemployment, 2009", tools=TOOLS,
        x_axis_location=None, y_axis_location=None
    )
    p.grid.grid_line_color = None
    p.patches('x', 'y', source=source, fill_alpha=0.7, line_color="white", line_width=0.5)
    html = file_html(p, CDN, "my plot")

    with open("/Users/Ziqi/Desktop/map.html", "w") as my_file:
        my_file.write(html)
    print ("exported")
