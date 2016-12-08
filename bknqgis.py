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
import os
#import pysal as ps
import numpy as np
import geopandas as gpd
import pandas as pd
from shapely.geometry import shape
import json
from bokeh.io import output_file, show
from bokeh.models import ColumnDataSource,GeoJSONDataSource,CategoricalColorMapper,HoverTool,PanTool, WheelZoomTool, BoxSelectTool,GMapPlot, GMapOptions,DataRange1d
from bokeh.plotting import figure
from bokeh.sampledata.sample_geojson import geojson
from bokeh.resources import CDN, INLINE
from bokeh.embed import file_html,notebook_div,components
from bokeh.charts.attributes import cat, color
from bokeh.models.glyphs import Patches, Line, Circle


class bknqgis:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        self.settings = {}
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

        #UI presetting - Ziqi
        self.dlg.lineEditGAPI.hide()
        self.dlg.lineEditZoom.hide()
        self.dlg.comboBoxMapType.hide()
        self.dlg.labelZoom.hide()
        self.dlg.labelMapType.hide()
        self.dlg.labelAPI.hide()
        self.dlg.GoogleCheckBox.stateChanged.connect(self.GoogleChecked)
        self.dlg.alphaSlider.valueChanged.connect(self.alphaSliderChange)
        self.dlg.lineEditAlpha.setText("0")
        self.dlg.lineEditAlpha.textEdited.connect(self.alphaTextChange)
        self.dlg.lineEditAlpha.setValidator(QIntValidator())
        self.dlg.lineEditZoom.setValidator(QIntValidator())
        self.dlg.lineEditPlotFrameWidth.setValidator(QIntValidator())
        self.dlg.leftMargin.setValidator(QIntValidator())
        self.dlg.rightMargin.setValidator(QIntValidator())
        self.dlg.topMargin.setValidator(QIntValidator())
        self.dlg.botMargin.setValidator(QIntValidator())
        self.dlg.radioButtonCDN.setChecked(True)
        self.dlg.comboBoxMapType.addItems(["roadmap", "satellite", "hybrid","terrain"])
        self.dlg.comboBoxToolPosition.addItems(["above","below","left","right","none"])
        self.dlg.comboBoxSizingMode.addItems(["fixed", "stretch_both", "scale_width", "scale_height", "scale_both"])
        self.dlg.lineEditZoom.setText("5")
        self.dlg.lineEditOutlineWidth.setText("0.5")
        #Export path
        self.dlg.lineEdit.clear()
        self.dlg.lineEdit.setText(os.path.expanduser('~'))
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
        #
        self.dlg.pushButtonBKBorderColor.clicked.connect(self.color_picker_border)
        self.dlg.pushButtonBKBorderColor.setStyleSheet("QWidget { background-color: %s}" % "white")
        self.dlg.pushButtonFrameColor.clicked.connect(self.color_picker_Frame)
        self.dlg.pushButtonFrameColor.setStyleSheet("QWidget { background-color: %s}" % "white")
        self.dlg.pushButtonBGColor.clicked.connect(self.color_picker_BG)
        self.dlg.pushButtonBGColor.setStyleSheet("QWidget { background-color: %s}" % "white")
        self.dlg.pushButtonOLColor.clicked.connect(self.color_picker_OL)
        self.dlg.pushButtonOLColor.setStyleSheet("QWidget { background-color: %s}" % "white")
        #
        self.dlg.loadSetting.clicked.connect(self.load_setting)


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
        filename = QFileDialog.getExistingDirectory(self.dlg, "Select output folder",os.path.expanduser('~'), QFileDialog.ShowDirsOnly)
        self.dlg.lineEdit.setText(filename)
        #Toggle google map options when checking - Ziqi
    def GoogleChecked(self):
        if self.dlg.GoogleCheckBox.isChecked():
            self.dlg.lineEditGAPI.show()
            self.dlg.lineEditZoom.show()
            self.dlg.comboBoxMapType.show()
            self.dlg.labelZoom.show()
            self.dlg.labelMapType.show()
            self.dlg.labelAPI.show()
        else:
            self.dlg.lineEditGAPI.hide()
            self.dlg.lineEditZoom.hide()
            self.dlg.comboBoxMapType.hide()
            self.dlg.labelZoom.hide()
            self.dlg.labelMapType.hide()
            self.dlg.labelAPI.hide()
    def alphaSliderChange(self):
        self.dlg.lineEditAlpha.setText(str(self.dlg.alphaSlider.value()))
    def alphaTextChange(self):
        if self.dlg.lineEditAlpha.text():
            self.dlg.alphaSlider.setValue(int(self.dlg.lineEditAlpha.text()))
    #Table functions for hover
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

    #Main function when clicking "export"
    #The setting dictionary is used to store all setting parameters
    def preview(self):
        selectedLayerIndex = self.dlg.comboBoxLayer.currentIndex()
        selectedLayer = self.dlg.comboBoxLayer.itemData(selectedLayerIndex)
        self.settings["layer"] = selectedLayer
        self.settings["field"] = self.dlg.valueFieldText.text()
        self.settings["outputFile"] = self.dlg.lineEdit.text()
        self.settings["width"] = int(self.dlg.lineEditWidth.text())
        self.settings["height"] = int(self.dlg.lineEditHeight.text())
        self.settings["ratioChecked"] = self.dlg.ratioCheckBox.isChecked()
        self.settings["title"] = self.dlg.lineEditTitle.text()
        self.settings["hoverFields"] = []
        self.settings["alpha"] = 100 - self.dlg.alphaSlider.value()
        self.settings["title"] = self.dlg.lineEditTitle.text()
        self.settings["outlineColor"] = self.dlg.pushButtonOLColor.text()
        self.settings["outlineWidth"] = float(self.dlg.lineEditOutlineWidth.text())
        self.settings["googleMapType"] = self.dlg.comboBoxMapType.currentText()
        self.settings["zoomLevel"] = int(self.dlg.lineEditZoom.text())
        self.settings["GoogleEnabled"] = self.dlg.GoogleCheckBox.isChecked()
        self.settings["GMAPIKey"] = self.dlg.lineEditGAPI.text()
        if self.dlg.radioButtonCDN.isChecked():
            self.settings["BokehJS"] = "CDN"
        if self.dlg.radioButtonINLINE.isChecked():
            self.settings["BokehJS"] = "INLINE"
        self.settings["background_fill_color"] = self.dlg.pushButtonBGColor.text()
        self.settings["background_fill_alpha"] = float(self.dlg.lineEditBGAlpha.text())
        self.settings["outline_line_alpha"] = float(self.dlg.lineEditFrameAlpha.text())
        self.settings["outline_line_width"] = int(self.dlg.lineEditPlotFrameWidth.text())
        self.settings["outline_line_color"] = self.dlg.pushButtonFrameColor.text()
        self.settings["border_fill_color"] = self.dlg.pushButtonBKBorderColor.text()
        self.settings["min_border_left"] = int(self.dlg.leftMargin.text())
        self.settings["min_border_right"] = int(self.dlg.rightMargin.text())
        self.settings["min_border_top"] = int(self.dlg.topMargin.text())
        self.settings["min_border_bottom"] = int(self.dlg.botMargin.text())
        self.settings["toolbar_location"] = self.dlg.comboBoxToolPosition.currentText()
        self.settings["sizing_mode"] = self.dlg.comboBoxSizingMode.currentText()

        for row in xrange(self.dlg.tableWidget.rowCount()):
            item0 = self.dlg.tableWidget.cellWidget(row, 0)
            item1 = self.dlg.tableWidget.item(row, 1)
            if item0:
                self.settings["hoverFields"].append([str(item0.itemData(item0.currentIndex()).name()),item1.text()])
            else:
                item0 = self.dlg.tableWidget.item(row, 0)
                self.settings["hoverFields"].append([item0.text(),item1.text()])
        if selectedLayer:
            self.bkExport(self.settings)

        messageBox = QMessageBox()
        messageBox.setWindowTitle( "Success" )
        messageBox.setText( "HTML Exported Successful")
        messageBox.exec_()
    #Color pickers
    def color_picker_border(self):
        colorDialog = QColorDialog()
        colorDialog.setOption(QColorDialog.ShowAlphaChannel, True)
        colorDialog.setOption(QColorDialog.DontUseNativeDialog, True)
        color = colorDialog.getColor()
        if color.isValid():
            self.dlg.pushButtonBKBorderColor.setStyleSheet("QWidget { background-color: %s}" % color.name())
            self.dlg.pushButtonBKBorderColor.setText(color.name())
    def color_picker_Frame(self):
        colorDialog = QColorDialog()
        colorDialog.setOption(QColorDialog.ShowAlphaChannel, True)
        colorDialog.setOption(QColorDialog.DontUseNativeDialog, True)
        color = colorDialog.getColor()
        if color.isValid():
            self.dlg.pushButtonFrameColor.setStyleSheet("QWidget { background-color: %s}" % color.name())
            self.dlg.pushButtonFrameColor.setText(color.name())
    def color_picker_BG(self):
        colorDialog = QColorDialog()
        colorDialog.setOption(QColorDialog.ShowAlphaChannel, True)
        colorDialog.setOption(QColorDialog.DontUseNativeDialog, True)
        color = colorDialog.getColor()
        if color.isValid():
            self.dlg.pushButtonBGColor.setStyleSheet("QWidget { background-color: %s}" % color.name())
            self.dlg.pushButtonBGColor.setText(color.name())
    def color_picker_OL(self):
        colorDialog = QColorDialog()
        colorDialog.setOption(QColorDialog.ShowAlphaChannel, True)
        colorDialog.setOption(QColorDialog.DontUseNativeDialog, True)
        color = colorDialog.getColor()
        if color.isValid():
            self.dlg.pushButtonOLColor.setStyleSheet("QWidget { background-color: %s}" % color.name())
            self.dlg.pushButtonOLColor.setText(color.name())

    #Load setting.json and update widgets
    def load_setting(self):
        filename = QFileDialog.getOpenFileName(self.dlg, "Select output file ","", '*.json')
        if filename:
            with open(filename, "r") as my_setting:
                settings = json.load(my_setting)
            #Basics:
                self.dlg.comboBoxLayer.setCurrentIndex(self.dlg.comboBoxLayer.findText(settings["layer"]))
                self.dlg.valueFieldText.setText(str(settings["field"]))
                self.dlg.lineEdit.setText(str(settings["outputFile"]))
                self.dlg.lineEditWidth.setText(str(settings["width"]))
                self.dlg.lineEditHeight.setText(str(settings["height"]))
                self.dlg.ratioCheckBox.setChecked(settings["ratioChecked"])
                self.dlg.lineEditTitle.setText(str(settings["title"]))
                self.dlg.lineEditOutlineWidth.setText(str(settings["outlineWidth"]))
                self.dlg.alphaSlider.setValue(100 - int(settings["alpha"]))
                self.dlg.pushButtonOLColor.setStyleSheet("QWidget { background-color: %s}" % settings["outlineColor"])
                self.dlg.pushButtonOLColor.setText(settings["outlineColor"])
                #Hover fields:
                self.deleteAllTable()
                for row in xrange(len(settings["hoverFields"])):
                    self.dlg.tableWidget.insertRow(row)
                    newComboBox = QComboBox()
                    label1 = QTableWidgetItem()
                    label1.setFlags(Qt.ItemIsEnabled)
                    label1.setText( settings["hoverFields"][row][0])
                    label2 = QTableWidgetItem()
                    label2.setText( settings["hoverFields"][row][1])
                    self.dlg.tableWidget.setItem(row, 0, label1)
                    self.dlg.tableWidget.setItem(row, 1, label2)

                #Advanced:
                #Google Maps
                self.dlg.GoogleCheckBox.setChecked(settings["GoogleEnabled"])
                self.dlg.lineEditZoom.setText(str(settings["zoomLevel"]))
                self.dlg.lineEditGAPI.setText(settings["GMAPIKey"])
                self.dlg.comboBoxMapType.setCurrentIndex(self.dlg.comboBoxMapType.findText(settings["googleMapType"]))
                #Other
                self.dlg.lineEditBGAlpha.setText(str(settings["background_fill_alpha"]))
                self.dlg.lineEditFrameAlpha.setText(str(settings["outline_line_alpha"]))
                self.dlg.lineEditPlotFrameWidth.setText(str(settings["outline_line_width"]))
                self.dlg.leftMargin.setText(str(settings["min_border_left"]))
                self.dlg.rightMargin.setText(str(settings["min_border_right"]))
                self.dlg.topMargin.setText(str(settings["min_border_top"]))
                self.dlg.botMargin.setText(str(settings["min_border_bottom"]))
                self.dlg.comboBoxToolPosition.setCurrentIndex(self.dlg.comboBoxToolPosition.findText(settings["toolbar_location"]))
                self.dlg.comboBoxSizingMode.setCurrentIndex(self.dlg.comboBoxSizingMode.findText(settings["sizing_mode"]))
                self.dlg.pushButtonFrameColor.setStyleSheet("QWidget { background-color: %s}" % settings["outline_line_color"])
                self.dlg.pushButtonFrameColor.setText(settings["outline_line_color"])
                self.dlg.pushButtonBKBorderColor.setStyleSheet("QWidget { background-color: %s}" % settings["border_fill_color"])
                self.dlg.pushButtonBKBorderColor.setText(settings["border_fill_color"])
                self.dlg.pushButtonBGColor.setStyleSheet("QWidget { background-color: %s}" % settings["background_fill_color"])
                self.dlg.pushButtonBGColor.setText(settings["background_fill_color"])
                if settings["BokehJS"] == "CDN":
                    self.dlg.radioButtonCDN.setChecked(True)
                    if settings["BokehJS"] == "INLINE":
                        self.dlg.radioButtonINLINE.setChecked(True)


    def onLayerChange(self, index):
        self.deleteAllTable()
        layer = self.dlg.comboBoxLayer.itemData(index) # gets selected layer
        print layer
        if layer:
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

    #The main procesisng function
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
                    try:
                        gdf2["class"][(gdf2["data"] == categories[i].value())] = i
                    except:
                        gdf2["class"][(gdf2["data"] == float(categories[i].value()))] = i

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

        if settings["toolbar_location"] == "none":
            TOOLS = ""
        else:
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
        if settings["GoogleEnabled"]:
            print ("Enable Google")
            map_options = GMapOptions(lat=np.nanmean([val for sublist in lats for val in sublist]),
                          lng=np.nanmean([val for sublist in lons for val in sublist]), map_type=settings["googleMapType"], zoom=settings["zoomLevel"])

            plot = GMapPlot(plot_width=width, plot_height=height,x_range=DataRange1d(), y_range=DataRange1d(), map_options=map_options,api_key = settings["GMAPIKey"])

            source_patches = source
            patches = Patches(xs='x', ys='y', fill_alpha=settings["alpha"]/100.0, line_color=settings["outlineColor"], line_width=settings["outlineWidth"],fill_color = {'field': 'category', 'transform': color_mapper})
            patches_glyph = plot.add_glyph(source_patches, patches)
            plot.add_tools(PanTool(), WheelZoomTool(), BoxSelectTool(), HoverTool())
        else:
            #plot_width=width, plot_height=height,
            plot = figure(
                title=settings["title"], tools=TOOLS,plot_width=width, plot_height=height,
                x_axis_location=None, y_axis_location=None
                )
            plot.grid.grid_line_color = None
            plot.patches('x', 'y', source=source, fill_alpha=settings["alpha"]/100.0, line_color=settings["outlineColor"], line_width=settings["outlineWidth"],fill_color = {'field': 'category', 'transform': color_mapper})

        plot.border_fill_color = settings["border_fill_color"]
        plot.background_fill_color = settings["background_fill_color"]
        plot.background_fill_alpha = settings["background_fill_alpha"]
        plot.outline_line_alpha = settings["outline_line_alpha"]
        plot.outline_line_color = settings["outline_line_color"]
        plot.outline_line_width = settings["outline_line_width"]
        if settings["toolbar_location"] == "none":
            plot.toolbar_location = None
        else:
            plot.toolbar_location = settings["toolbar_location"]
        plot.min_border_left = settings["min_border_left"]
        plot.min_border_right = settings["min_border_right"]
        plot.min_border_top = settings["min_border_top"]
        plot.min_border_bottom = settings["min_border_bottom"]
        plot.sizing_mode = settings["sizing_mode"]

        if settings["hoverFields"]:
            hover = plot.select_one(HoverTool)
            hover.point_policy = "follow_mouse"
            hover.tooltips = [
                #(field, "@data")
                #("(Long, Lat)", "($x, $y)"),
                ]
            for hField in settings["hoverFields"]:
                temp = "@"+hField[0]
                hover.tooltips.append((hField[1],temp))

        if settings["BokehJS"] == "CDN":
            print ("CDN")
            html = file_html(plot, CDN, "my plot")
        elif settings["BokehJS"] == "INLINE":
            print ("INLINE")
            html = file_html(plot, INLINE, "my plot")
        with open(self.settings["outputFile"] + "/map.html", "w") as my_html:
            my_html.write(html)
        settings["layer"] = settings["layer"].name()
        print settings
        with open(self.settings["outputFile"] + "/settings.json", 'w') as fp:
            json.dump(settings, fp)
