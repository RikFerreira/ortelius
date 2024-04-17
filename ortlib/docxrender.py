# -*- coding: utf-8 -*-

from qgis.core import *
from qgis.utils import iface

import jinja2
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
import base64
# import qrcode
import os
import io

from .qgiscontext import QgisContext

class DocxRender:
    def __init__(self, template_file: str, temp_dir) -> None:
        if not isinstance(template_file, str):
            raise TypeError('Template file must be a str object!')

        self.input_template = DocxTemplate(template_file)

        self.jinja_env = jinja2.Environment()
        self.jinja_env.filters['x_for_match'] = self.x_for_match
        self.jinja_env.filters['export_qgs_print_layout'] = self.export_qgs_print_layout
        self.jinja_env.filters['export_picture_from_base64'] = self.export_picture_from_base64
        self.jinja_env.filters['render_picture_from_path'] = self.render_picture_from_path
        self.jinja_env.filters['multiple_check_boxes'] = self.multiple_check_boxes

        self.temp_dir = temp_dir

    def render(self, context) -> None:
        if isinstance(context, QgisContext):
            ctx_dict = context.get_dict()
        else:
            raise TypeError('Unknown object specified as Context!')

        self.input_template.reset_replacements()
        self.input_template.render(ctx_dict, self.jinja_env)

    def export(self, path: str) -> None:
        if not isinstance(path, str):
            raise TypeError('Path must be a str object!')

        self.input_template.save(path)

    def multiple_check_boxes(self, value, domain):
        type_value = type(value)

        if not isinstance(domain, tuple):
            raise TypeError('Domain is not a tuple!')

        # if not isinstance(domain[0], type_value):
        #     raise TypeError('Tuple elements are from a different type than the given value!')

        print_dict = {a: '☑' if b else '☐' for a, b in zip(domain, [x == value for x in domain])}

        string_buff = io.StringIO()

        for key, value in print_dict.items():
            string_buff.write(f'{value}\t{key}\n')

        return string_buff.getvalue()

    def x_for_match(self, value, compare):
        return "X" if value == compare else ""

    def export_picture_from_base64(self, base64string, filename, output_dir = None):
        if output_dir is None:
            output_dir = self.temp_dir

        output_file = os.path.join(output_dir, filename)

        with open(output_file, 'wb') as fout:
            fout.write(base64.decodebytes(base64string))

        return output_file

    def export_qgs_print_layout(self, layout_dict, feature_dict, output_dir = None):
        if layout_dict['layout_atlas'].enabled():
            layout_dict['layout_atlas'].beginRender()
            layout_dict['layout_atlas'].seekTo(feature_dict['feature_obj'])
            layout_dict['layout_atlas'].refreshCurrentFeature()

        if not output_dir:
            output_dir = self.temp_dir

        # output_file = os.path.join(output_dir, self.output_name.format(**self.filename_var_space) + '_' + layout_dict['layout_obj'].name() + '.' + 'png')
        output_file = os.path.join(output_dir, f'{layout_dict["layout_name"]}_{feature_dict["feature_id"]}.png')

        exporter = QgsLayoutExporter(layout_dict['layout_obj'])
        exporter.exportToImage(output_file, QgsLayoutExporter.ImageExportSettings())

        return output_file

    def render_picture_from_path(self, path, width = None, height = None):
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

    def convert_valuemap(self, value, layer_dict, field_name) -> str:
        layer = layer_dict['layer_obj']
        field_idx = layer.fields().indexFromName(field_name)

        try:
            config_map = layer.editorWidgetSetup(field_idx).config()['map']
        except:
            return ''

        value_map_dict = {value: key for dict in config_map for key, value in dict.items()}

        return value_map_dict[value]

    # TODO: def exportQrCode(self, feature):
        # This is the logic of the method
        # Transform feature to WGS 84 (EPSG: 4326)
        # Extract centroid coordinates (multipart are a single feature)
        # Format as following: "lat, long". Precision 5
        # Create QR Code from the previous string
        # Export it to temp folder

    # TODO: Image edition using imagemagick

    # TODO: def mount_processing_dict(self):
