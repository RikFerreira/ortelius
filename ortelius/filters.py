import os
import io

def multiple_check_boxes(self, value, domain):
    print_dict = {a: '☑' if b else '☐' for a, b in zip(domain, [x == value for x in domain])}

    string_buff = io.StringIO()

    for key, value in print_dict.items():
        string_buff.write(f'{value}\t{key}\n')

    return string_buff.getvalue()

def xForMatch(self, value, compare):
    return "X" if value == compare else ""

def exportPictureFromBase64(self, base64string, filename, output_dir = None):
    if output_dir is None:
        output_dir = self.temp_dir

    output_file = os.path.join(output_dir, filename)

    with open(output_file, 'wb') as fout:
        fout.write(base64.decodebytes(base64string))

    return output_file

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
