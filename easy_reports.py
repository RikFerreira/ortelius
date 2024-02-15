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

from PyQt5.QtCore import QDateTime, QDate, QTime, QByteArray

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .easy_reports_dialog import EasyReportsDialog
# from .tasks.render_document import RenderDoc
import os.path

import time
from itertools import compress
from functools import reduce
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
import jinja2
import json
import io
import base64
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
            pass

    def setup_interface(self):
        # TODO: Reset project directory here
        # Project level attributes
        self.pj_instance = QgsProject.instance()

        self.working_dir = QgsExpressionContextUtils.projectScope(self.pj_instance).variable('project_home')
        os.chdir(self.working_dir)

        # Set project variables
        QgsExpressionContextUtils.setProjectVariable(self.pj_instance, 'tpf_feature_index', -1)

        # Set temporary folder
        self.temp_dir = QgsProcessingUtils.tempFolder()

        # List all layers
        self.pjLayers = [layer for layer in self.pj_instance.mapLayers().values()]
        layers_name = [layer.name() for layer in self.pjLayers]

        self.dlg.qtTabWidget.setCurrentIndex(0)

        self.dlg.qtInputLayer.clear()
        self.dlg.qtInputLayer.addItems(layers_name)
        self.dlg.qtInputLayer.setCurrentText(self.iface.activeLayer().name())

        self.dlg.qtQgsInputTemplate.setFilePath(QgsExpressionContextUtils.projectScope(self.pj_instance).variable('tpf_template_file'))

        self.dlg.qtQgsOutputDir.setFilePath(QgsExpressionContextUtils.projectScope(self.pj_instance).variable('tpf_output_dir'))

        self.dlg.qtOutputName.clear()
        self.dlg.qtOutputName.insert(QgsExpressionContextUtils.projectScope(self.pj_instance).variable('tpf_output_name'))

        # Setup context dictionary
        self.environment = dict()
        self.env_global = dict()

        # Setup custom filters
        self.jinja_env = jinja2.Environment()
        self.jinja_env.filters['xForMatch'] = self.xForMatch
        self.jinja_env.filters['exportPrintLayout'] = self.exportPrintLayout
        self.jinja_env.filters['exportPictureFromBase64'] = self.exportPictureFromBase64
        self.jinja_env.filters['renderPictureFromPath'] = self.renderPictureFromPath
        # self.jinja_env.filters['renderPictureFromBase64'] = self.renderPictureFromBase64
        self.jinja_env.filters['multiple_check_boxes'] = self.multiple_check_boxes

        self.update_interface()

    def update_interface(self):
        # Input layer
        self.input_layer = self.pj_instance.mapLayersByName(self.dlg.qtInputLayer.currentText())[0]

        self.echo_log(f'Camada mapeada: {self.input_layer}', True)

        self.pj_relations = self.pj_instance.relationManager().relations()

    def echo_log(self, message, breakbefore = False):
        if breakbefore:
            self.dlg.qtLogConsole.append('')
        self.dlg.qtLogConsole.append(time.strftime('%d.%m.%Y' + ' - ' + '%H' + ':' + '%M' + ':' + '%S'))
        self.dlg.qtLogConsole.append(message)
        self.dlg.qtLogConsole.update()

    def check_input(self):
        if not os.path.isfile(self.dlg.qtQgsInputTemplate.filePath()):
            raise FileNotFoundError('No template specified!')

        if not os.path.isdir(self.dlg.qtQgsOutputDir.filePath()):
            raise NotADirectoryError('No output directory specified!')

        if not self.dlg.qtOutputName.text():
            raise ValueError('No output name specified!')

        self.output_formats = dict()
        self.output_formats['docx'] = self.dlg.qtOutputDocx.checkState()
        self.output_formats['pdf'] = self.dlg.qtOutputPdf.checkState()
        self.output_formats['odt'] = self.dlg.qtOutputOdt.checkState()
        self.output_formats['html'] = self.dlg.qtOutputHtml.checkState()

        if not reduce(lambda a, b: a or b, list(self.output_formats.values())):
            raise ValueError('No output format specified!')

        self.input_layer_name = self.dlg.qtInputLayer.currentText()
        self.input_templateFile = self.dlg.qtQgsInputTemplate.filePath()
        self.input_template = DocxTemplate(self.input_templateFile)
        self.output_dir = self.dlg.qtQgsOutputDir.filePath()
        self.output_name = self.dlg.qtOutputName.text()

        if self.dlg.qtSelectedFeaturesOnly.isChecked():
            self.features_iterable = list(self.input_layer.getSelectedFeatures())
        else:
            self.features_iterable = list(self.input_layer.getFeatures())

        if len(self.features_iterable) == 0:
            raise ValueError('No feature selected!')

        QgsExpressionContextUtils.setProjectVariable(self.pj_instance, 'tpf_template_file', self.input_templateFile)
        QgsExpressionContextUtils.setProjectVariable(self.pj_instance, 'tpf_output_dir', self.output_dir)
        QgsExpressionContextUtils.setProjectVariable(self.pj_instance, 'tpf_output_name', self.output_name)

        return True

    def mount_global_dict(self):
        env_global = {
            'global': {
                'project_obj': QgsProject.instance(),
                'mapCanvas': iface.mapCanvas(),
                'project_bbox': [
                    iface.mapCanvas().extent().xMinimum(),
                    iface.mapCanvas().extent().yMinimum(),
                    iface.mapCanvas().extent().xMaximum(),
                    iface.mapCanvas().extent().yMaximum()
                ],
                'global_vars': {x: QgsExpressionContextUtils.globalScope().variable(x) for x in QgsExpressionContextUtils.globalScope().variableNames()},
                'project_vars': {x: QgsExpressionContextUtils.projectScope(QgsProject.instance()).variable(x) for x in QgsExpressionContextUtils.projectScope(QgsProject.instance()).variableNames()}
            }
        }

        return env_global

    def mount_layer_dict(self, layer):
        env_layer = {
            'layer': {
                'layer_obj': layer,
                'layer_type': get_layer_type(layer.type()),
                'layer_geometry_type': get_geometry_type(layer.geometryType()),
                'layer_name': layer.name(),
                'layer_id': layer.id(),
                'layer_source': layer.sourceName(),
                'layer_extent': layer.extent(),
                'layer_bbox': [
                    layer.extent().xMinimum(),
                    layer.extent().yMinimum(),
                    layer.extent().xMaximum(),
                    layer.extent().yMaximum()
                ]
            }
        }

        return env_layer

    def mount_feature_dict(self, feature, layer):
        env_feature = dict()

        env_feature.update(self.mount_layer_dict(layer))

        env_feature.update({
            'feature': {
                'feature_obj': feature,
                'feature_id': feature.id(),
                'feature_wkt': feature.geometry().asWkt() if layer.isSpatial() and not feature.geometry().isNull() else None,
                'feature_geojson': feature.geometry().asJson() if layer.isSpatial() and not feature.geometry().isNull() else None,
                'feature_extent': feature.geometry().boundingBox() if layer.isSpatial() and not feature.geometry().isNull() else None,
                'feature_centroid': feature.geometry().centroid().asPoint() if layer.isSpatial() and not feature.geometry().isNull() else None
            }
        })

        # TODO: Figure out a way to the user to choose if the value is the real or the alias
        attr_dict = {}
        if layer.type() == QgsMapLayerType.VectorLayer:
            for field in layer.fields().toList():
                value = feature[field.name()]

                if isinstance(value, QDateTime):
                    value = value.toString('yyyy/MM/dd HH:mm:ss')
                if isinstance(value, QDate):
                    value = value.toString('yyyy/MM/dd')
                if isinstance(value, QTime):
                    value = value.toString('HH:mm:ss')
                if isinstance(value, QByteArray):
                    value = value.toBase64().data()

                attr_dict[field.name()] = value

        env_feature['feature'].update(attr_dict)

        for relation in self.pj_relations.values():
            related_features = list(relation.getRelatedFeatures(feature))
            related_layer = relation.referencingLayer()

            if len(related_features) == 0:
                continue

            relation_list = list()
            for rel_feat in related_features:
                relation_list.append(self.mount_feature_dict(rel_feat, related_layer))

            env_feature.update({related_layer.name(): relation_list})

        return env_feature

    def mount_layouts_dict(self):
        self.lyt_manager = self.pj_instance.layoutManager()

        env_layouts = {
            'layouts': dict()
        }

        for lyt in self.lyt_manager.printLayouts():
            env_layouts['layouts'].update({lyt.name(): {'layout_obj': lyt, 'layout_atlas': lyt.atlas()}})

        return env_layouts

    # TODO: def mount_processing_dict(self):

    def run_expression(self, expr_string):
        expression = QgsExpression(expr_string)

        if not expression.isValid():
            raise ValueError('Expression not valid!')

        return expression.evaluate()

    # TODO: Image edition using imagemagick


    def exportPrintLayout(self, layout_dict, feature_dict, output_dir = None):
        if layout_dict['layout_atlas'].enabled():
            layout_dict['layout_atlas'].beginRender()
            layout_dict['layout_atlas'].seekTo(feature_dict['feature_obj'])
            layout_dict['layout_atlas'].refreshCurrentFeature()

        if not output_dir:
            output_dir = self.temp_dir

        output_file = os.path.join(output_dir, self.output_name.format(**self.filename_var_space) + '_' + layout_dict['layout_obj'].name() + '.' + 'png')

        exporter = QgsLayoutExporter(layout_dict['layout_obj'])
        exporter.exportToImage(output_file, QgsLayoutExporter.ImageExportSettings())

        return output_file

    # # # # # # # # # # # # # # # #
    # Custom filters              #
    # # # # # # # # # # # # # # # #

    # TODO: def exportQrCode(self, feature):
        # This is the logic of the method
        # Transform feature to WGS 84 (EPSG: 4326)
        # Extract centroid coordinates (multipart are a single feature)
        # Format as following: "lat, long". Precision 5
        # Create QR Code from the previous string
        # Export it to temp folder

    def renderPictureFromPath(self, path, width = None, height = None):
        # TODO: This method does not work well with portrait images. The method rotates the image before render.

        section = self.input_template.get_docx().sections[0]
        section_width = (section.page_width - (section.left_margin + section.right_margin)) * 1.0 / 36000

        if width <= 1:
            image_width = Mm(section_width) * width
        else:
            image_width = Mm(width)

        if height:
            image_height = Mm(height)
        else:
            image_height = height

        return InlineImage(self.input_template, path, width = image_width, height = image_height)

    def exportPictureFromBase64(self, base64string, filename, output_dir = None):
        if output_dir is None:
            output_dir = self.temp_dir

        output_file = os.path.join(output_dir, filename)

        with open(output_file, 'wb') as fout:
            fout.write(base64.decodebytes(base64string))

        return output_file

    def xForMatch(self, value, compare):
        return "X" if value == compare else ""

    def multiple_check_boxes(self, value, domain):
        print_dict = {a: '☑' if b else '☐' for a, b in zip(domain, [x == value for x in domain])}

        string_buff = io.StringIO()

        for key, value in print_dict.items():
            string_buff.write(f'{value}\t{key}\n')

        return string_buff.getvalue()

    def render_docx(self):
        for main_feature in self.features_iterable:
            # TODO: Figure out why this loop runs 3 times
            # TODO: The creation of the dictionary and the docx export must be inside a QgsTask class. The plugin responsivity relies on this!!!
            QgsExpressionContextUtils.setProjectVariable(self.pj_instance, 'tpf_feature_index', main_feature.id())

            context = dict()

            context.update(self.mount_global_dict())
            context.update(self.mount_feature_dict(main_feature, self.pj_instance.mapLayersByName(self.input_layer_name)[0]))
            context.update(self.mount_layouts_dict())

            self.filename_var_space = context['feature']

            # print(json.dumps(self.context, indent = 4, default = str))

            self.input_template.reset_replacements()
            self.input_template.render(context, self.jinja_env)
            self.input_template.save(os.path.join(self.output_dir, self.output_name.format(**self.filename_var_space) + '.docx'))

            self.progress_bar_value += self.progress_bar_step
            self.dlg.qtProgressBar.setValue(self.progress_bar_value)

        self.dlg.qtProgressBar.setValue(self.dlg.qtProgressBar.maximum())

        iface.messageBar().pushMessage('TPF Easy Reports', f'All {len(self.features_iterable)} features exported!',level=Qgis.Info)

        pass

    def run_export(self):
        self.dlg.qtTabWidget.setCurrentIndex(1)

        try:
            self.check_input()
        except ValueError as e:
            iface.messageBar().pushMessage('TPF Easy Reports', f'ValueError: {e}', level = Qgis.Critical)
        else:
            # TODO: Parallelize the progress bar
            self.progress_bar_step = round((self.dlg.qtProgressBar.maximum() - self.dlg.qtProgressBar.minimum())) / len(self.features_iterable)
            self.progress_bar_value = 0
            self.dlg.qtProgressBar.setValue(self.progress_bar_value)

            self.render_docx()

            # tsk_render_docx = QgsTask.fromFunction('render_docx', self.render_docx)
            # # self.tsk_mgr = QgsTaskManager()
            # # self.tsk_mgr.addTask(tsk_render_docx)
            # QgsApplication.taskManager().addTask(tsk_render_docx)

def get_layer_type(layer_type):
    # TODO: This method must be replaced byu a match-case statement as soon as QGIS 3.34 becomes the LTS
    if layer_type == QgsMapLayerType.VectorLayer:
        type = "vector"
    elif layer_type == QgsMapLayerType.RasterLayer:
        type = "raster"
    elif layer_type == QgsMapLayerType.PluginLayer:
        type = "plugin"
    elif layer_type == QgsMapLayerType.MeshLayer:
        type = "mesh"
    elif layer_type == QgsMapLayerType.VectorTileLayer:
        type = "vector_tile"
    elif layer_type == QgsMapLayerType.AnnotationLayer:
        type = "annotation"
    else:
        type = "unknown"

    return type

def get_geometry_type(geometry_type):
    # TODO: This method must be replaced byu a match-case statement as soon as QGIS 3.34 becomes the LTS
    if geometry_type == QgsWkbTypes.PointGeometry:
        type = "point"
    elif geometry_type == QgsWkbTypes.LineGeometry:
        type = "line"
    elif geometry_type == QgsWkbTypes.PolygonGeometry:
        type = "polygon"
    elif geometry_type == QgsWkbTypes.UnknownGeometry:
        type = "unknown"
    elif geometry_type == QgsWkbTypes.NullGeometry:
        type = "null_geometry"
    else:
        type = "unknown"

    return type
