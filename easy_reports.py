# -*- coding: utf-8 -*-
"""
/***************************************************************************
 EasyReports
                                 A QGIS plugin
 This plugin performs a mail merge like for QGIS layers.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2023-08-29
        git sha              : $Format:%H$
        copyright            : (C) 2023 by TPF Engenharia
        email                : rik.alves@tpfe.com.br
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
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, QSize
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import *
from qgis.utils import iface

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .easy_reports_dialog import EasyReportsDialog
import os.path

import time
from itertools import compress
from functools import reduce
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
import jinja2
import json
# import qrcode

class EasyReports:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'EasyReports_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&TPF Easy Reports')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('EasyReports', message)


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
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/easy_reports/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'TPF Easy Reports'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&TPF Easy Reports'),
                action)
            self.iface.removeToolBarIcon(action)


    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = EasyReportsDialog()

        self.setup_interface()

        self.dlg.qtInputLayer.currentIndexChanged.connect(self.update_interface)
        self.dlg.qtExportReports.clicked.connect(self.run_export)

        # show the dialog
        self.dlg.show()

        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            self.populate_relations()

    def setup_interface(self):
        # Project level attributes
        self.pjInstance = QgsProject.instance()

        # Set project variables
        QgsExpressionContextUtils.setProjectVariable(self.pjInstance, 'tpf_feature_index', -1)

        # Set temporary folder
        self.tempFolder = QgsProcessingUtils.tempFolder()

        # List all layers
        self.pjLayers = [layer for layer in self.pjInstance.mapLayers().values()]
        layers_name = [layer.name() for layer in self.pjLayers]

        self.dlg.qtTabWidget.setCurrentIndex(0)

        self.dlg.qtInputLayer.clear()
        self.dlg.qtInputLayer.addItems(layers_name)

        self.dlg.qtInputLayer.setCurrentText(self.iface.activeLayer().name())

        # Setup custom filters
        self.jinja_env = jinja2.Environment()
        self.jinja_env.filters['renderPictureFromPath'] = self.renderPictureFromPath
        self.jinja_env.filters['xForMatch'] = self.xForMatch
        self.jinja_env.filters['exportPrintLayout'] = self.exportPrintLayout

        # self.jinja_env.filters['renderPictureFromBase64'] = self.renderPictureFromBase64
        # self.jinja_env.filters['multipleCheckBoxes'] = self.multipleCheckBoxes

        self.update_interface()

    def update_interface(self):
        # Input layer
        self.inputLayerName = self.dlg.qtInputLayer.currentText()

        self.echo_log(f'Camada mapeada: {self.inputLayerName}', True)

        self.populate_layouts()
        self.populate_relations()


    def populate_relations(self):
        pj_relations = self.pjInstance.relationManager().relations()
        self.pjRelations = {key: pj_relations[key] for key in pj_relations}

        # Boolean flags for position of input in relations. Do not consider relations that do not refer to input_layer
        input_layer_is_parent = [relations.referencedLayer().name() == self.inputLayerName for relations in list(self.pjRelations.values())]
        input_layer_is_child = [relations.referencingLayer().name() == self.inputLayerName for relations in list(self.pjRelations.values())]

        self.relationsWhereInputIsParent = list(compress(list(self.pjRelations.values()), input_layer_is_parent))
        self.relationsWhereInputIsChild = list(compress(list(self.pjRelations.values()), input_layer_is_child))

        # Get child and parent layers and layer names
        child_layers = [relation.referencingLayer() for relation in self.relationsWhereInputIsParent]
        child_layers_name = [child.name() for child in child_layers]
        parent_layers = [relation.referencedLayer() for relation in self.relationsWhereInputIsChild]
        parent_layers_name = [parent.name() for parent in parent_layers]

        # Get all unrelated layers to present to user in dialog
        unrelated_layers_name = [layer_name for layer_name in [layer_name.name() for layer_name in self.pjLayers] if layer_name not in [self.inputLayerName] + child_layers_name + parent_layers_name]
        unrelated_layers = [self.pjInstance.mapLayersByName(layer_name)[0] for layer_name in unrelated_layers_name]
        unrelated_vector_layers = [layer.name() for layer in unrelated_layers if isinstance(layer, QgsVectorLayer)]
        unrelated_raster_layers = [layer.name() for layer in unrelated_layers if isinstance(layer, QgsRasterLayer)]

        self.dlg.qtParentList.clear()
        self.dlg.qtChildList.clear()
        self.dlg.qtListUnrelatedVector.clear()
        self.dlg.qtListUnrelatedRaster.clear()

        self.dlg.qtParentList.addItems(child_layers_name)
        self.dlg.qtChildList.addItems(parent_layers_name)
        self.dlg.qtListUnrelatedVector.addItems(unrelated_vector_layers)
        self.dlg.qtListUnrelatedRaster.addItems(unrelated_raster_layers)

        self.dlg.qtParentList.selectAll()
        self.dlg.qtChildList.selectAll()
        self.dlg.qtListUnrelatedVector.selectAll()
        self.dlg.qtListUnrelatedRaster.clearSelection()

        self.echo_log(f'Updated relations\n' \
                      f"Child layers: {len(child_layers_name)}\n" \
                      f"Parent layers: {len(parent_layers_name)}\n" \
                      f"Unrelated vector layers: {len(unrelated_vector_layers)}\n" \
                      f"Unrelated raster layers: {len(unrelated_raster_layers)}\n")


    def populate_layouts(self):
        pj_print_layouts = {layout.name(): layout for layout in self.pjInstance.layoutManager().layouts()}

        self.dlg.qtListPrintLayouts.clear()
        self.dlg.qtListPrintLayouts.addItems(list(pj_print_layouts.keys()))
        self.dlg.qtListPrintLayouts.selectAll()

        self.echo_log(f'Updated print layouts\n' \
                      f'Print layouts: {len(pj_print_layouts)}')

    def echo_log(self, message, breakbefore = False):
        if breakbefore:
            self.dlg.qtLogConsole.append('')
        self.dlg.qtLogConsole.append(time.strftime('%d.%m.%Y' + ' - ' + '%H' + ':' + '%M' + ':' + '%S'))
        self.dlg.qtLogConsole.append(message)
        self.dlg.qtLogConsole.update()

    def check_input(self):
        if not os.path.isfile(self.dlg.qtQgsInputTemplate.filePath()):
            self.echo_log('ERROR: No template specified!')
            return False

        if not os.path.isdir(self.dlg.qtQgsOutputDir.filePath()):
            self.echo_log('ERROR: No output directory specified!')
            return False

        if not self.dlg.qtOutputName.text():
            self.echo_log('ERROR: No output name specified!')
            return False

        self.outputFormats = dict()
        self.outputFormats['docx'] = self.dlg.qtOutputDocx.checkState()
        self.outputFormats['pdf'] = self.dlg.qtOutputPdf.checkState()
        self.outputFormats['odt'] = self.dlg.qtOutputOdt.checkState()
        self.outputFormats['html'] = self.dlg.qtOutputHtml.checkState()

        if not reduce(lambda a, b: a or b, list(self.outputFormats.values())):
            self.echo_log('ERROR: No output format specified!')
            return False

        self.inputLayerName = self.dlg.qtInputLayer.currentText()
        self.inputTemplateFile = self.dlg.qtQgsInputTemplate.filePath()
        self.inputTemplate = DocxTemplate(self.inputTemplateFile)
        self.outputDir = self.dlg.qtQgsOutputDir.filePath()
        self.outputName = self.dlg.qtOutputName.text()

        self.childLayersName = [item.text() for item in self.dlg.qtParentList.selectedItems()]
        self.parentLayersName = [item.text() for item in self.dlg.qtChildList.selectedItems()]
        self.unrelatedVectorLayersName = [item.text() for item in self.dlg.qtListUnrelatedVector.selectedItems()]
        self.unrelatedRasterLayersName = [item.text() for item in self.dlg.qtListUnrelatedRaster.selectedItems()]

        self.pjPrintLayoutsName = [item.text() for item in self.dlg.qtListPrintLayouts.selectedItems()]

        self.echo_log(f'Current input consists of:\n' \
                      f"Child layers: {len(self.childLayersName)}\n" \
                      f"Parent layers: {len(self.parentLayersName)}\n" \
                      f"Unrelated vector layers: {len(self.unrelatedVectorLayersName)}\n" \
                      f"Unrelated raster layers: {len(self.unrelatedRasterLayersName)}\n" \
                      f"Print layouts: {len(self.pjPrintLayoutsName)}\n")

        return True

    def exportPrintLayout(self, layoutParams, figWidth = 1.0, isAtlas = True, outputFolder = None, driver = 'png'):
        # TODO: This function needs to be splitted in a function for the render and a function for the exporter. It is necessary as there must be an option for display the numeric scale. The current workflow has two subsequent procedures for determine figure width. Solving the former may fix this flaw
        self.lytManager = self.pjInstance.layoutManager()

        printLayoutName = layoutParams[0]
        feature = layoutParams[1]

        layout = self.lytManager.layoutByName(layoutParams[0])

        if isAtlas:
            layout.atlas().beginRender()
            layout.atlas().seekTo(feature)
            layout.atlas().refreshCurrentFeature()
        
        layoutPageSize = layout.pageCollection().page(0).pageSize()
        aspectRatio = layoutPageSize.width() / layoutPageSize.height()

        width = Mm(tpl_get_page_width(self.inputTemplate)) * figWidth
        height = width / aspectRatio
        
        if outputFolder is None:
            outputFolder = self.tempFolder
        # outputFile = os.path.join(outputFolder, str(feature.id()) + '_' + printLayoutName + '.' + 'png')
        outputFile = os.path.join(outputFolder, self.outputName.format(**self.context) + '_' + printLayoutName + '.' + 'png')

        # layout.pageCollection().page(0).setPageSize(QgsLayoutSize(width, height))
        exporter = QgsLayoutExporter(layout)
        exporter.exportToImage(outputFile, QgsLayoutExporter.ImageExportSettings())
        return outputFile
        print(exporter)
        lytImage = exporter.renderPageToImage(0, QSize(width, height), 300)
        print(lytImage)
        if lytImage.save(outputFile, driver):
            iface.messageBar().pushCritical("E aí?", "DEU CERTO!")
        else:
            iface.messageBar().pushCritical("E aí?", "DEU ERRADO!")

        print(layoutParams)
        print(isAtlas)
        print(figWidth)
        print(outputFolder)
        print(driver)
        print(outputFile)

        return outputFile

        # FEATURE: Jinja custom filter for image formatting from docx template

        # SECURITY_FEATURE: Assure that output format is supported by QGIS
        # if not driver in ('png', 'jpg'):
        #     return False

        if outputFolder is None:
            outputFolder = self.tempFolder

        outputFile = os.path.join(outputFolder, str(feature.id()) + '_' + printLayoutName + '.' + 'png')

        # mapItem = QgsProject().instance().layoutManager().layoutByName(printLayoutName).itemById('map')
        mapItem = self.lytManager.layoutByName(printLayoutName).itemById('map')
        mapItem.zoomToExtent(scale_rectangle(feature.geometry().boundingBox(), scale))

        mapLayoutScale = mapItem.mapUnitsToLayoutUnits()

        layoutSize = QgsLayoutSize((mapItem.extent().xMaximum() - mapItem.extent().xMinimum()) * mapLayoutScale, (mapItem.extent().yMaximum() - mapItem.extent().yMinimum()) * mapLayoutScale)
        self.lytManager.layoutByName(printLayoutName).pageCollection().pages()[0].setPageSize(layoutSize)

        exporter = QgsLayoutExporter(self.lytManager.layoutByName(printLayoutName))
        exporter.exportToImage(outputFile, QgsLayoutExporter.ImageExportSettings())

        # return InlineImage(self.inputTemplate, outputFile, width = width, height = height)
        return outputFile

    ## Futuro: implementar opção JPG ou PNG
    # def exportPrintLayout(self, printLayoutName, scale = 1.1, feature, outputFolder = None, driver = 'png'):
        # # FEATURE: Jinja custom filter for image formatting from docx template

        # # SECURITY_FEATURE: Assure that output format is supported by QGIS
        # # if not driver in ('png', 'jpg'):
        # #     return False

        # if outputFolder is None:
        #     outputFolder = self.tempFolder

        # outputFile = os.path.join(outputFolder, str(feature.id()) + '_' + printLayoutName + '.' + 'png')

        # # mapItem = QgsProject().instance().layoutManager().layoutByName(printLayoutName).itemById('map')
        # mapItem = self.pjInstance.layoutManager().layoutByName(printLayoutName).itemById('map')
        # mapItem.zoomToExtent(scale_rectangle(feature.geometry().boundingBox(), scale))

        # mapLayoutScale = mapItem.mapUnitsToLayoutUnits()

        # layoutSize = QgsLayoutSize((mapItem.extent().xMaximum() - mapItem.extent().xMinimum()) * mapLayoutScale, (mapItem.extent().yMaximum() - mapItem.extent().yMinimum()) * mapLayoutScale)
        # QgsProject().instance().layoutManager().layoutByName(printLayoutName).pageCollection().pages()[0].setPageSize(layoutSize)

        # exporter = QgsLayoutExporter(QgsProject().instance().layoutManager().layoutByName(printLayoutName))
        # exporter.exportToImage(outputFile, QgsLayoutExporter.ImageExportSettings())

        # # return InlineImage(self.inputTemplate, outputFile, width = width, height = height)
        # return outputFile

    # def exportQrCode(self, feature):
        # This is the logic of the method
        # Transform feature to WGS 84 (EPSG: 4326)
        # Extract centroid coordinates (multipart are a single feature)
        # Format as following: "lat, long". Precision 5
        # Create QR Code from the previous string
        # Export it to temp folder

    # # # # # # # # # # # # # # # #
    # Custom filters              #
    # # # # # # # # # # # # # # # #
    def renderPictureFromPath(self, path, width = None, height = None):
        return InlineImage(self.inputTemplate, path, width = Mm(tpl_get_page_width(self.inputTemplate)) * width, height = height)

    def renderPictureFromBase64(self, path, width, height):
        # TODO: Currently, the plugin does not support input of layers with Base64 fields. This must be fixed in order to export reports from GIS based on ESRI FileGeodatabase driver
        return -1

    def xForMatch(self, value, compare):
        return "X" if value == compare else ""

    def multipleCheckBoxes(self, value, domain):
        return -1

    def run_export(self):
        self.dlg.qtTabWidget.setCurrentIndex(4)

        if self.check_input():

            self.progressBarStep = round((self.dlg.qtProgressBar.maximum() - self.dlg.qtProgressBar.minimum())) / len(list(self.pjInstance.mapLayersByName(self.inputLayerName)[0].getFeatures()))
            self.progressBar = 0
            self.dlg.qtProgressBar.setValue(self.progressBar)

            i = 1
            for mainFeature in self.pjInstance.mapLayersByName(self.inputLayerName)[0].getSelectedFeatures():
                print(mainFeature.id())
                QgsExpressionContextUtils.setProjectVariable(self.pjInstance, 'tpf_feature_index', mainFeature.id())

                self.context = qgsFeatureListToDict([mainFeature], False)

                for relation_name in zip(self.childLayersName, self.relationsWhereInputIsParent):
                    relatedFeatures = qgsFeatureListToDict([x for x in relation_name[1].getRelatedFeatures(mainFeature)])
                    if len(relatedFeatures) == 1:
                        relatedFeatures = relatedFeatures[0]
                    self.context[relation_name[0]] = relatedFeatures

                for relation_name in zip(self.parentLayersName, self.relationsWhereInputIsChild):
                    relatedFeatures = qgsFeatureListToDict([x for x in relation_name[1].getRelatedFeatures(mainFeature)])
                    if len(relatedFeatures) == 1:
                        relatedFeatures = relatedFeatures[0]
                    self.context[relation_name[0]] = relatedFeatures
                    # self.context[relation_name[0]] = qgsFeatureListToDict([x for x in relation_name[1].getRelatedFeatures(mainFeature)])

                # exportedLayouts = {layoutName: self.exportPrintLayout(mainFeature, layoutName, Mm(tpl_get_page_width(self.inputTemplate))) for layoutName in self.pjPrintLayoutsName}
                exportedLayouts = {layoutName: (layoutName, mainFeature) for layoutName in self.pjPrintLayoutsName}

                self.context.update(exportedLayouts)

                print(self.context)

                self.inputTemplate.reset_replacements()
                self.inputTemplate.render(self.context, self.jinja_env)
                self.inputTemplate.save(os.path.join(self.outputDir, self.outputName.format(**self.context)))

                self.progressBar += self.progressBarStep
                self.dlg.qtProgressBar.setValue(self.progressBar)

                i += 1

            self.dlg.qtProgressBar.setValue(self.dlg.qtProgressBar.maximum())



# Geopackage types (typeNames) supported by QGIS: ['Integer64', 'String', 'Integer', 'Real', 'Boolean', 'Date', 'String', 'DateTime', 'Binary', 'JSON', 'JSON', 'JSON', 'JSON']
def qgsFeatureListToDict(featureList, listDict = True):
    if len(featureList) == 0:
        return []

    features = []
    for feature in featureList:
        tempDict = json.loads(QgsJsonUtils.exportAttributes(feature))
        # Can't remember why I put this for loop in here, but I suspect it is important
        for key, value in tempDict.items():
            tempDict[key] = "" if value is None else value
        features.append(tempDict)

    if not listDict:
        features = features[0]

    return features

def tpl_get_page_width(template, ratio=1.0):
    section = template.get_docx().sections[0]
    return (section.page_width - (section.left_margin + section.right_margin)) * ratio / 36000

def scale_rectangle(rectangle, scale = 1.0):
    rect_dim = {'width': rectangle.xMaximum() - rectangle.xMinimum(), 'height': rectangle.yMaximum() - rectangle.yMinimum()}
    return QgsRectangle(rectangle.center().x() - rect_dim['width']/2.0 * scale, rectangle.center().y() - rect_dim['height']/2.0 * scale, rectangle.center().x() + rect_dim['width']/2.0 * scale, rectangle.center().y() + rect_dim['height']/2.0 * scale)

def qgsAttributesToPythonTypes(qgsFields, qgsAttributes):
    qgsType = field.typeName()