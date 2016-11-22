# -*- coding: utf-8 -*-
"""
/***************************************************************************
 bknqgis
                                 A QGIS plugin
 Link Bokeh to QGIS
                              -------------------
        begin                : 2016-10-31
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Ziqi Li
        email                : liziqi1992@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import QgsMessageLog
import resources
from bknqgis_dialog import bknqgisDialog
import os.path
#import pysal as ps
import numpy as np
import geopandas as gpd
import pandas as pd
#import shapely as shp
from shapely.geometry import shape
import json
from bokeh.io import output_file, show
from bokeh.models import ColumnDataSource,GeoJSONDataSource,CategoricalColorMapper,HoverTool,GMapPlot, GMapOptions
from bokeh.plotting import figure
from bokeh.sampledata.sample_geojson import geojson
from bokeh.resources import CDN, INLINE
from bokeh.embed import file_html,notebook_div,components
from bokeh.charts.attributes import cat, color


class bknqgis:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'bknqgis_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = bknqgisDialog()
        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&bknqgis')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'bknqgis')
        self.toolbar.setObjectName(u'bknqgis')
        #Export path
        self.dlg.lineEdit.clear()
        self.dlg.lineEdit.setText('/Users/Ziqi/Desktop/bokeh-map.html')
        self.dlg.outputBTN.clicked.connect(self.select_output_file)
        self.dlg.previewBTN.clicked.connect(self.preview)
        self.dlg.comboBoxLayer.activated.connect(self.onLayerChange)
        #Size Fields
        self.dlg.lineEditWidth.textEdited.connect(self.onWidthChange)
        self.dlg.lineEditHeight.textEdited.connect(self.onHeightChange)
        self.dlg.lineEditWidth.setValidator(QIntValidator())
        self.dlg.lineEditHeight.setValidator(QIntValidator())
        self.dlg.lineEditWidth.setMaxLength(4)
        self.dlg.lineEditHeight.setMaxLength(4)
        #ProgressBar
        self.dlg.progressBar.setValue(0)
        self.dlg.progressBar.setMinimum(0)
        self.dlg.progressBar.setMaximum(100)
        self.dlg.ratioCheckBox.setChecked(True)
        #Table
        self.dlg.delAllBTN.clicked.connect(self.deleteAllTable)
        self.dlg.addRowBTN.clicked.connect(self.addRowTable)
        self.dlg.delRowBTN.clicked.connect(self.delRowTable)
        self.dlg.tableWidget.setColumnCount(2)
        self.dlg.tableWidget.setHorizontalHeaderLabels(["Fields","Labels"])
        self.dlg.tableWidget.setColumnWidth(0, 150)
        header = self.dlg.tableWidget.horizontalHeader()
        header.setStretchLastSection(True)
        self.dlg.htmlRB.setChecked(True)
        '''
        self.dlg.htmlRB.clicked.connect(self.onHtmlRBClicked)
        self.dlg.jupyterRB.clicked.connect(self.onjupyterRBClicked)
        '''

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        return QCoreApplication.translate('bknqgis', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        if status_tip is not None:
            action.setStatusTip(status_tip)
        if whats_this is not None:
            action.setWhatsThis(whats_this)
        if add_to_toolbar:
            self.toolbar.addAction(action)
        if add_to_menu:
            self.iface.addPluginToWebMenu(
                self.menu,
                action)
        self.actions.append(action)
        return action

    def initGui(self):
        icon_path = ':/plugins/bknqgis/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'bknqgis'),
            callback=self.run,
            parent=self.iface.mainWindow())

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginWebMenu(
                self.tr(u'&bknqgis'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def run(self):
        """Run method that performs all the real work"""
        #
        self.dlg.comboBoxLayer.clear()
        self.onLayerChange
        #self.dlg.progressBar.setValue(0)
        layers = self.iface.legendInterface().layers()
        #layer_list = []
        for layer in layers:
            if layer.geometryType() == 2:
                self.dlg.comboBoxLayer.addItem(layer.name(), layer)
        #self.dlg.comboBoxLayer.addItems(layer_list)
        selectedLayerIndex = self.dlg.comboBoxLayer.currentIndex()
        self.onLayerChange(selectedLayerIndex)
        selectedLayer = self.dlg.comboBoxLayer.itemData(selectedLayerIndex)
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            pass

    def select_output_file(self):
        filename = QFileDialog.getSaveFileName(self.dlg, "Select output file ","", '*.html')
        self.dlg.lineEdit.setText(filename)

    def deleteAllTable(self):
        self.dlg.tableWidget.setRowCount(0)

    def addRowTable(self):
        rowPosition = self.dlg.tableWidget.rowCount()
        self.dlg.tableWidget.insertRow(rowPosition)
        selectedLayerIndex = self.dlg.comboBoxLayer.currentIndex()
        selectedLayer = self.dlg.comboBoxLayer.itemData(selectedLayerIndex)
        newComboBox = QComboBox()
        for field in selectedLayer.pendingFields():
            newComboBox.addItem(field.name(), field) # lists layer fields
        label = QTableWidgetItem()
        self.dlg.tableWidget.setCellWidget(rowPosition, 0, newComboBox)
        self.dlg.tableWidget.setItem(rowPosition, 1, label)

    def delRowTable(self):
        rowPosition = self.dlg.tableWidget.rowCount()
        self.dlg.tableWidget.setRowCount(rowPosition - 1)

    def preview(self):
        file_path = "/Users/Ziqi/Desktop/map.html"
        selectedLayerIndex = self.dlg.comboBoxLayer.currentIndex()
        selectedLayer = self.dlg.comboBoxLayer.itemData(selectedLayerIndex)
        #selectedFieldIndex = self.dlg.comboBoxField.currentIndex()
        #selectedField = self.dlg.comboBoxField.itemData(selectedFieldIndex)

        settings = {}
        settings["layer"] = selectedLayer
        settings["field"] = self.dlg.valueFieldText.text()
        settings["outputFile"] = self.dlg.lineEdit.text()
        settings["width"] = int(self.dlg.lineEditWidth.text())
        settings["height"] = int(self.dlg.lineEditHeight.text())
        settings["title"] = "Bokeh Test Map"
        settings["hoverFields"] = []
        for row in xrange(self.dlg.tableWidget.rowCount()):
            item0 = self.dlg.tableWidget.cellWidget(row, 0)
            item1 = self.dlg.tableWidget.item(row, 1)
            settings["hoverFields"].append([str(item0.itemData(item0.currentIndex()).name()),str(item1.text())])

        self.bkExport(settings)

        messageBox = QMessageBox()
        messageBox.setWindowTitle( "Success" )
        messageBox.setText( "HTML Exported Successful")
        messageBox.exec_()

    def onLayerChange(self, index):
        self.deleteAllTable()
        layer = self.dlg.comboBoxLayer.itemData(index) # gets selected layer
        renderer = layer.rendererV2()
        if renderer.usedAttributes():
            self.dlg.valueFieldText.setText(renderer.usedAttributes()[0])
        else:
            self.dlg.valueFieldText.setText("")
        ratio = layer.extent().width()/layer.extent().height()
        self.dlg.lineEditWidth.setText("800")
        self.dlg.lineEditHeight.setText(str(int(int(self.dlg.lineEditWidth.text())/ratio)))

    def onWidthChange(self):
        if self.dlg.ratioCheckBox.isChecked():
            print ("checked")
            selectedLayerIndex = self.dlg.comboBoxLayer.currentIndex()
            selectedLayer = self.dlg.comboBoxLayer.itemData(selectedLayerIndex)
            ratio = selectedLayer.extent().width()/selectedLayer.extent().height()
            if self.dlg.lineEditWidth.text():
                self.dlg.lineEditHeight.setText(str(int(int(self.dlg.lineEditWidth.text())/ratio)))
            else:
                self.dlg.lineEditHeight.setText("")
            print (self.dlg.lineEditHeight.text(),self.dlg.lineEditWidth.text())

    def onHeightChange(self):
        if self.dlg.ratioCheckBox.isChecked():
            selectedLayerIndex = self.dlg.comboBoxLayer.currentIndex()
            selectedLayer = self.dlg.comboBoxLayer.itemData(selectedLayerIndex)
            ratio = selectedLayer.extent().width()/selectedLayer.extent().height()
            if self.dlg.lineEditHeight.text():
                self.dlg.lineEditWidth.setText(str(int(int(self.dlg.lineEditHeight.text())*ratio)))
            else:
                self.dlg.lineEditWidth.setText("")
            print (self.dlg.lineEditHeight.text(),self.dlg.lineEditWidth.text())

    def onHtmlRBClicked(self):
        self.dlg.htmlRB.setChecked(True)
        self.dlg.jupyterRB.setChecked(False)
        print "htmlClicked"
    def onjupyterRBClicked(self):
        self.dlg.htmlRB.setChecked(False)
        self.dlg.jupyterRB.setChecked(True)
        print "Jupyter"

    def gpd_bokeh(self,df):
        """Convert geometries from geopandas to bokeh format"""
        nan = float('nan')
        lons = []
        lats = []
        for i,shape in enumerate(df.geometry.values):
            if shape.geom_type == 'MultiPolygon':
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
                xy = np.array(list(shape.exterior.coords))
                xs = xy[:,0].tolist()
                ys = xy[:,1].tolist()
                lons.append(xs)
                lats.append(ys)

        return lons,lats

    def bkExport(self,settings):
    #layer = iface.legendInterface().layers()[0]
        layer = settings["layer"]
        field = settings["field"]
        gdfList = []
        total = float(layer.featureCount())
        counter = 0
        for feature in layer.getFeatures():
            counter = counter + 1
            self.dlg.progressBar.setValue(counter/total*100)
            featJsonString = feature.geometry().geometry().asJSON(17)
            featJson = json.loads(featJsonString)
            df = {}
            df["geometry"] = shape(featJson)
            if field:
                df["data"] = feature[field]
            else:
                df["data"] = 0
            df["class"] = -1
            for hField in settings["hoverFields"]:
                df[hField[0]] = feature[hField[0]]
            gdf = gpd.GeoDataFrame([df])
            gdfList.append(gdf)

        gdf2 = gpd.GeoDataFrame(pd.concat(gdfList,ignore_index=True))

        lons, lats = self.gpd_bokeh(gdf2)
        data = list(gdf2["data"])
        #map settings
        #ratio = layer.extent().width()/layer.extent().height()
        #height = int(layer.extent().height()*20)
        height = settings["height"]
        width = settings["width"]
        renderer = layer.rendererV2()
        if renderer.type() == 'singleSymbol':
            print "singleSymbol"
            color = renderer.symbol().color().name()
            color_mapper = CategoricalColorMapper(factors=[-1], palette=[color])
        elif renderer.type() == 'categorizedSymbol':
            print "categorizedSymbol"
            categories = renderer.categories()
            for i in xrange(len(categories)):
                if categories[i].value():
                    gdf2["class"][(gdf2["data"] == categories[i].value())] = i
            colorPalette = [symbol.color().name() for symbol in renderer.symbols()]
            color_mapper = CategoricalColorMapper(factors=sorted(list(gdf2["class"].unique())), palette=colorPalette)
        elif renderer.type() == 'graduatedSymbol':
            print "graduatedSymbol"
            ranges = renderer.ranges()
            gdf2["class"] = map(renderer.legendKeyForValue,gdf2["data"])
            colorPalette = [symbol.color().name() for symbol in renderer.symbols()]
            color_mapper = CategoricalColorMapper(factors=sorted(list(gdf2["class"].unique())), palette=colorPalette)
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
        for hField in settings["hoverFields"]:
            source.add(gdf2[hField[0]],name=hField[0])

        #plot_width=width, plot_height=height,
        p = figure(
            title=settings["title"], tools=TOOLS,plot_width=width, plot_height=height,
            x_axis_location=None, y_axis_location=None
        )
        p.grid.grid_line_color = None
        p.patches('x', 'y', source=source, fill_alpha=1, line_color="black", line_width=0.5,fill_color = {'field': 'category', 'transform': color_mapper},)


        if settings["hoverFields"]:
            hover = p.select_one(HoverTool)
            hover.point_policy = "follow_mouse"
            hover.tooltips = [
                #(field, "@data")
                #("(Long, Lat)", "($x, $y)"),
            ]
            for hField in settings["hoverFields"]:
                temp = "@"+hField[0]
                hover.tooltips.append((hField[1],temp))

        if self.dlg.htmlRB.isChecked():
            print ("HTML")
            html = file_html(p, CDN, "my plot")
            with open(settings["outputFile"], "w") as my_html:
                my_html.write(html)
        elif self.dlg.embedRB.isChecked():
            print ("Embbed")
            script, div = components(p)
        elif self.dlg.jupyterRB.isChecked():
            print ("Jupyter Notebook")
            div = notebook_div(p)
            with open(settings["outputFile"], "w") as my_div:
                my_div.write(div)
