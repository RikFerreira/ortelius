# -*- coding: utf-8 -*-

import jinja2
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
import base64
# import qrcode
import os
import io

class DocxRender:
    def __init__(self, template_file) -> None:
        self.input_template = DocxTemplate(template_file)

        self.jinja_env = jinja2.Environment()
        self.jinja_env.filters['xForMatch'] = self.xForMatch
        self.jinja_env.filters['exportPrintLayout'] = self.exportPrintLayout
        self.jinja_env.filters['exportPictureFromBase64'] = self.exportPictureFromBase64
        self.jinja_env.filters['renderPictureFromPath'] = self.renderPictureFromPath
        self.jinja_env.filters['multiple_check_boxes'] = self.multiple_check_boxes

    def render(self, context) -> None:
        if isinstance(context, QgisContext):
            ctx_dict = context.get_dict()
        # elif isinstance(context, dict):
        #     ctx_dict = context
        else:
            raise TypeError('Unknown object specified as context!')

        self.input_template.reset_replacements()
        self.input_template.render(ctx_dict, self.jinja_env)

    def export(self, path: str) -> None:
        if not isinstance(path, str):
            raise TypeError('Path must be a str object!')

        self.input_template.save(path)

    def multiple_check_boxes(self, value, domain):
        print_dict = {a: '☑' if b else '☐' for a, b in zip(domain, [x == value for x in domain])}

        string_buff = io.StringIO()

        for key, value in print_dict.items():
            string_buff.write(f'{value}\t{key}\n')

        return string_buff.getvalue()

    def x_for_match(self, value, compare):
        return "X" if value == compare else ""

    def export_picture_from_base_64(self, base64string, filename, output_dir = None):
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

        output_file = os.path.join(output_dir, self.output_name.format(**self.filename_var_space) + '_' + layout_dict['layout_obj'].name() + '.' + 'png')

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
