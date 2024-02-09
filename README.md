# TPF Easy Reports

## Showcase

## Installation

### Dependencies

These dependencies must be installed manually in OSGeo4W Shell:

- docxtpl==0.16.7
- jinja2==2.11.2
- docx==0.2.4
- qrcode==7.4.2

```
pip install docxtpl jinja2 docx qrcode
```

## Basic usage

## Getting help

- Rik Ferreira Alves
  - rik.alves@tpfe.com.br

## Documentation

### Jinja 2 placeholders and statements

- `{{ variable }}`: An element from the dictionary named `variable` will be used to fill this placeholder
- `{% if <condition> %}`, `{% else %}`, `{% endif %}`: An if statement can be built inside the template using these tags
- `{%- if <condition> -%}`, `{%- else -%}`, `{%- endif -%}`: An if statement, but escaping the ENTER or the SHIFT+ENTER from MS Word
- `{% for <x> in <list> %}`, `{% endfor %}`: A for statement can be built inside the template using these tags. Useful to iterate over child features

### Structure

Each document has a complex dictionary with attributes extracted from the relational model centered in the reference layer. You can access all the attributes of the reference layer by calling the attribute name. Other dimenions are stores as dictionaries at the first level of the context dictionary, so:

- Context
  - `global`
  - `layer`
  - `feature`
    - `feature_obj`: QgsFeature object
    - `feature_id`: Feature ID (equivalent of `$id` in QGIS expression)
    - `feature_wkt`: Feature geometry as a well-known text string
    - `feature_geojson`: Feature geometry as GeoJSON string
    - `feature_extent`: QgsRectangle of the feature extent
    - `feature_centroid`: QgsPointXY object of the feature centroid
    - All the attributes of the feature are called by their name, not their alias
  - `related layer name`
    - `layer`
    - `feature`
    - `related layer name and so on...`
  - `layouts`
    - `layout name`
      - `layout_obj`: QgsPrintLayout object
      - `layout_atlas`: QgsLayoutAtlas object

#### Sample context dictionary

```
    "global": {
    },
    "layer": {
    },
    "feature": {
    },
    "IntLin": [
        {
            "layer": {...},
            "feature": {...}
        },
        {},
        {}
    ],
    "IntPoli": [...]
    "IntPto": [...]
    "LocAre": [...]
    "LocVer": [...]
    "Nascente": [...]
    "URUCUIA_PIALBE_V2__ATTACH": [...]
    "layouts": {
        "QgsMapaLocCad": {
            "layout_obj": "<qgis._core.QgsPrintLayout object at 0x000001566C6EB4C0>",
            "layout_atlas": "<qgis._core.QgsLayoutAtlas object at 0x000001566FE7B430>"
        },
        ...
    }
```

### Filters

Filters are custom functions designed to extend the capabilities of the DOCX reports. Here is a list of the custom filters implemented by this plugin:

- `exportPrintLayout`: Expects a `layout` dictionary, renders the map and returns a path pointing to the exported PNG figure. Parameters:
  - `layout_dict`: A `layout` dictionary
  - `feature_dict`: A `feature` dictionary
  - `output_dir = None`: If specified, export the layout to a folder. If not, export the layout to a temporary directory
- `exportPictureFromBase64`: Expects a base64 string and returns the path of the exported image
  - `base64string`: A base64 string
  - `filename`:  An output file name
  - `output_dir`: If specified, export the picture to a folder. If not, export the picture to a temporary directory
- `renderPictureFromPath`: Expects a file path and returns an `InlineImage` object
  - `path`: The path of the image
  - `width`: If a number between 0 and 1 is specified, the width is a percentage of the page width available (without margins). If a number greater than 1 is specified, the width is a absolute value
  - `height = None`: If specified, forces a height value to the image. If not, preserves the aspect ratio of the image
- `xForMatch`:
- `multipleCheckBoxes`:

### Further reading

- Although there is a Sphinx API documentation for PyQGIS, QGIS C++ API Reference is preferrable as it reveals the big picture of QGIS classes.
  - [C++ API Reference](https://api.qgis.org/api/index.html)
  - [Python API Reference](https://qgis.org/pyqgis/3.0/)
