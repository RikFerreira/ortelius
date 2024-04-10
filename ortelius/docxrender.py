# -*- coding: utf-8 -*-

import jinja2
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
import base64
# import qrcode

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
