# -*- coding: utf-8 -*-
# Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, QSize
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import *
from qgis.utils import iface

from PyQt5.QtCore import QDateTime, QDate, QTime, QByteArray

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .ortelius_dialog import OrteliusDialog
# from .ortelius.render_document import RenderDoc
# from .ortelius.context import Context
import os.path

import time
import json
from itertools import compress
from functools import reduce
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
import traceback

from . import ortlib

# TODO: Make a method to show field alias instead of field name (option to display field alias in parenthesis)
# To access the value map as a dictionary, we must access it with the following code
# idx = layer.fields().indexFromName("PresArvores")
# value_map = layer.editorWidgetSetup(idx).config()["map"]
# So, flatten the dict:
# {key: value for dict in value_map for key, value in dict.items()}

class Ortelius:
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
        self.menu = self.tr(u'&Ortelius')

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

        icon_path = ':/plugins/ortelius/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Ortelius'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Ortelius'),
                action)
            self.iface.removeToolBarIcon(action)

    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = OrteliusDialog()

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
        # Project level attributes
        self.pj_instance = QgsProject.instance()

        # Set plugin directories of interest
        self.temp_dir = QgsProcessingUtils.tempFolder()
        self.working_dir = QgsExpressionContextUtils.projectScope(self.pj_instance).variable('project_home')
        os.chdir(self.working_dir)

        # Set project variables
        QgsExpressionContextUtils.setProjectVariable(self.pj_instance, 'ortelius_feature_index', -1)

        # List all layers
        self.pj_layers = {layer.id(): (layer.name(), layer) for layer in self.pj_instance.mapLayers().values()}

        self.dlg.qtTabWidget.setCurrentIndex(0)

        self.dlg.qtInputLayer.clear()
        self.dlg.qtInputLayer.addItems(list(self.pj_layers))
        self.dlg.qtInputLayer.setCurrentText(self.iface.activeLayer().id())

        default_setup = QgsExpressionContextUtils.projectScope(self.pj_instance).variable('ortelius_default_setup')
        try:
            self.defaults = default_setup
        except:
            with open(os.path.join(QgsApplication.qgisSettingsDirPath(), 'python/plugins/ortelius', 'defaults', 'cfg'), 'r') as defaults_json:
                self.defaults = json.load(defaults_json)

        self.dlg.qtInputLayer.setCurrentText(self.defaults['input']['qtInputLayer'])
        self.dlg.qtQgsInputTemplate.setFilePath(self.defaults['input']['qtQgsInputTemplate'])
        self.dlg.qtSelectedFeaturesOnly.setChecked(self.defaults['input']['qtSelectedFeaturesOnly'])

        self.dlg.qtQgsOutputDir.setFilePath(self.defaults['output']['qtQgsOutputDir'])
        self.dlg.qtOutputName.clear()
        self.dlg.qtOutputName.insert(self.defaults['output']['qtOutputName'])

        self.dlg.qtOutputDocx.setChecked(self.defaults['formats']['docx'])
        self.dlg.qtOutputPdf.setChecked(self.defaults['formats']['pdf'])
        self.dlg.qtOutputOdt.setChecked(self.defaults['formats']['odt'])
        self.dlg.qtOutputHtml.setChecked(self.defaults['formats']['html'])

        self.dlg.qtSaveJSON.setChecked(self.defaults['options']['json'])
        self.dlg.qtSaveLogFile.setChecked(self.defaults['options']['log'])

        # Setup context dictionary
        self.environment = dict()
        self.env_global = dict()

        self.update_interface()

    def update_interface(self):
        self.input_layer = self.pj_layers[self.dlg.qtInputLayer.currentText()][1]

        self.pj_relations = self.pj_instance.relationManager().relations()

    def echo_log(self, message, breakbefore = False):
        if breakbefore:
            self.dlg.qtLogConsole.append('')

        self.dlg.qtLogConsole.append(time.strftime('%d.%m.%Y' + ' - ' + '%H' + ':' + '%M' + ':' + '%S'))
        self.dlg.qtLogConsole.append(f'> {message}')
        self.dlg.qtLogConsole.update()

    def check_input(self):
        if not os.path.isfile(self.dlg.qtQgsInputTemplate.filePath()):
            raise FileNotFoundError('No template specified!')

        if not os.path.isdir(self.dlg.qtQgsOutputDir.filePath()):
            raise NotADirectoryError('No output directory specified!')

        if not self.dlg.qtOutputName.text():
            raise ValueError('No output name specified!')

        if not reduce(lambda a, b: a or b, list(self.defaults['formats'].values())):
            raise ValueError('No output format specified!')

        self.input_layer_name = self.dlg.qtInputLayer.currentText()
        self.input_template_file = self.dlg.qtQgsInputTemplate.filePath()
        self.input_template = DocxTemplate(self.input_template_file)
        self.output_dir = self.dlg.qtQgsOutputDir.filePath()
        self.output_name = self.dlg.qtOutputName.text()

        if self.dlg.qtSelectedFeaturesOnly.isChecked():
            self.features_iterable = list(self.input_layer.getSelectedFeatures())
        else:
            self.features_iterable = list(self.input_layer.getFeatures())

        if len(self.features_iterable) == 0:
            raise ValueError('No feature selected!')

        return True

    def save_json(self, ctx, filename):
        ctx_json = ctx.get_json()
        json_dir = os.path.join(self.output_dir, 'JSON')

        with open(os.path.join(json_dir, f'{filename}.json'), 'w') as out_file:
            out_file.write(ctx_json)

    def save_log(self):
        with open(os.path.join(self.output_dir, 'log.txt'), 'w') as out_file:
            out_file.write(self.dlg.qtLogConsole.toPlainText())

    def run_export(self):
        self.dlg.qtTabWidget.setCurrentIndex(1)

        self.defaults['input']['qtInputLayer'] = self.dlg.qtInputLayer.currentText()
        self.defaults['input']['qtQgsInputTemplate'] = self.dlg.qtQgsInputTemplate.filePath()
        self.defaults['input']['qtSelectedFeaturesOnly'] = self.dlg.qtSelectedFeaturesOnly.isChecked()

        self.defaults['output']['qtQgsOutputDir'] = self.dlg.qtQgsOutputDir.filePath()
        self.defaults['output']['qtOutputName'] = self.dlg.qtOutputName.text()

        self.defaults['formats']['docx'] = self.dlg.qtOutputDocx.isChecked()
        self.defaults['formats']['pdf'] = self.dlg.qtOutputPdf.isChecked()
        self.defaults['formats']['odt'] = self.dlg.qtOutputOdt.isChecked()
        self.defaults['formats']['html'] = self.dlg.qtOutputHtml.isChecked()

        self.defaults['options']['json'] = self.dlg.qtSaveJSON.isChecked()
        self.defaults['options']['log'] = self.dlg.qtSaveLogFile.isChecked()

        QgsExpressionContextUtils.setProjectVariable(self.pj_instance, 'ortelius_default_setup', self.defaults)

        try:
            self.check_input()
        except Exception as e:
            iface.messageBar().pushMessage('Ortelius', f'Error: {e}', level = Qgis.Critical)
            return

        # TODO: Parallelize the progress bar
        self.progress_bar_step = round((self.dlg.qtProgressBar.maximum() - self.dlg.qtProgressBar.minimum())) / len(self.features_iterable)
        self.progress_bar_value = 0
        self.dlg.qtProgressBar.setValue(self.progress_bar_value)

        try:
            context = ortlib.QgisContext(self.iface, self.pj_instance)
            docx = ortlib.DocxRender(self.input_template_file, self.temp_dir)
        except Exception as e:
            self.echo_log(f'ERROR: {str(e)}\n{traceback.print_last()}')
            return

        for file_format in [x.upper() for x in self.defaults['formats'] if self.defaults['formats'][x]] + (['JSON'] if self.defaults['options']['json'] else []):
            if not os.path.exists(os.path.join(self.output_dir, file_format)):
                os.mkdir(os.path.join(self.output_dir, file_format))

        self.echo_log(f'Reference layer:\n\t{self.input_layer.name()}\n\t{self.input_layer.id()}\n\t{len(self.features_iterable)} features to be exported.', True)

        for i, main_feature in enumerate(self.features_iterable):
            QgsExpressionContextUtils.setProjectVariable(self.pj_instance, 'ortelius_feature_index', main_feature.id())
            self.echo_log(f'({i+1}/{len(self.features_iterable)}) Feature {main_feature.id()}')

            try:
                context.mount(self.input_layer, main_feature)
                docx.render(context)
                docx.export(os.path.join(self.output_dir, 'DOCX', self.output_name.format(**context.get_dict()['feature']['attributes']) + '.docx'))

                if self.defaults['options']['json']:
                    self.save_json(context, self.output_name.format(**context.get_dict()['feature']['attributes']))
            except Exception as e:
                self.echo_log(f'ERROR: {str(e)}\n{traceback.print_last()}')
                continue

            self.echo_log(f'Feature {main_feature.id()} exported!\nFile name: {self.output_name.format(**context.get_dict()["feature"]["attributes"])}.')

        if self.defaults['options']['log']:
            self.save_log()

        self.echo_log(f'All {len(self.features_iterable)} selected features exported!')
