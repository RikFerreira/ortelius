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
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import *
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
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            self.populate_relations()
            print(f'1: {self.dlg.qtInputLayer.currentText()}')
    def setup_interface(self):
        # Project level attributes
        self.pjInstance = QgsProject.instance()
        # List all layers
        self.pjLayers = [layer for layer in self.pjInstance.mapLayers().values()]
        layers_name = [layer.name() for layer in self.pjLayers]
        self.dlg.qtTabWidget.setCurrentIndex(0)
        self.dlg.qtInputLayer.clear()
        self.dlg.qtInputLayer.addItems(layers_name)
        self.dlg.qtInputLayer.setCurrentText(self.iface.activeLayer().name())
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
        if not self.dlg.qtOutputName:
            self.echo_log('ERROR: No output name specified!')
            return False
        self.outputFormats = dict()
        self.outputFormats['docx'] = self.dlg.qtOutputDocx.checkState()
        self.outputFormats['pdf'] = self.dlg.qtOutputPdf.checkState()
        self.outputFormats['odt'] = self.dlg.qtOutputOdt.checkState()
        self.outputFormats['html'] = self.dlg.qtOutputHtml.checkState()
        if not reduce(lambda a, b: a or b, list(self.outputFormats.values())):
            self.echo_log('ERROR: No output format specified!')
            return False1
        self.inputLayerName = self.dlg.qtInputLayer.currentText()
        self.inputTemplateFile = self.dlg.qtQgsInputTemplate.filePath()
        self.inputTemplate = DocxTemplate(self.inputTemplateFile)
        self.outputDir = self.dlg.qtQgsOutputDir.filePath()
        self.outputName = self.dlg.qtOutputName.text()
        self.childLayersName = [item.text() for item in self.dlg.qtParentList.selectedItems()]
        print(list(self.childLayersName))
        self.parentLayersName = self.dlg.qtChildList.selectedItems()
        self.unrelatedVectorLayersName = self.dlg.qtListUnrelatedVector.selectedItems()
        self.unrelatedRasterLayersName = self.dlg.qtListUnrelatedRaster.selectedItems()
        self.pjPrintLayoutsName = self.dlg.qtListPrintLayouts.selectedItems()
        self.echo_log(f'Current input consists of:\n' \
                      f"Child layers: {len(self.childLayersName)}\n" \
                      f"Parent layers: {len(self.parentLayersName)}\n" \
                      f"Unrelated vector layers: {len(self.unrelatedVectorLayersName)}\n" \
                      f"Unrelated raster layers: {len(self.unrelatedRasterLayersName)}\n" \
                      f"Print layouts: {len(self.pjPrintLayoutsName)}\n")
        return True
    def run_export(self):
        self.dlg.qtTabWidget.setCurrentIndex(4)
        if self.check_input():
            print(self.__dict__)
            self.progressBarStep = round((self.dlg.qtProgressBar.maximum() - self.dlg.qtProgressBar.minimum())) / len(list(self.pjInstance.mapLayersByName(self.inputLayerName)[0].getFeatures()))
            self.progressBar = 0
            self.dlg.qtProgressBar.setValue(self.progressBar)
            for mainFeature in self.pjInstance.mapLayersByName(self.inputLayerName)[0].getFeatures():
                self.context = mainFeature.__geo_interface__['properties']
                for relation_name in zip(self.childLayersName, self.relationsWhereInputIsParent):
                    self.context[relation_name[0]] = [x.__geo_interface__['properties'] for x in relation_name[1].getRelatedFeatures(mainFeature)]
                for relation_name in zip(self.parentLayersName, self.relationsWhereInputIsChild):
                    self.context[relation_name[0]] = [x.__geo_interface__['properties'] for x in relation_name[1].getRelatedFeatures(mainFeature)]
                # context = {key: value for key, value in }
                print(self.context)
                # ## --> Exportar layouts aqui
                self.inputTemplate.reset_replacements()
                self.inputTemplate.render(self.context)
                self.inputTemplate.save(os.path.join(self.outputDir, self.outputName.format(**self.context)))
                print(os.path.join(self.outputDir, self.outputName.format(**self.context)))
                self.progressBar += self.progressBarStep
                self.dlg.qtProgressBar.setValue(self.progressBar)
            self.dlg.qtProgressBar.setValue(self.dlg.qtProgressBar.maximum())
# i = 1
# for main_feature in input_layer.getFeatures():
#     context = main_feature.__geo_interface__['properties']
#     for relation_name in zip(child_layers_name, relations_where_input_is_parent):
#         context[relation_name[0]] = [x.__geo_interface__['properties'] for x in relation_name[1].getRelatedFeatures(main_feature)]
#     for relation_name in zip(parent_layers_name, relations_where_input_is_child):
#         context[relation_name[0]] = [x.__geo_interface__['properties'] for x in relation_name[1].getRelatedFeatures(main_feature)]
#     exported_layouts = {layout_name: export_print_layout(main_feature, layout_name, Mm(tpl_get_page_width(doc)), docx_template = doc) for layout_name in pj_print_layouts.keys()}
#     context.update(exported_layouts)
#     print(context.keys())
#     doc.reset_replacements()
#     doc.render(context)
#     doc.save(f'{out_dir}/output_{i}.docx')
#     i += 1

