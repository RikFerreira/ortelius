# TPF Easy Reports

## Showcase

## Installation

## Basic usage

## Getting help

- Rik Ferreira Alves
  - rik.alves@tpfe.com.br

## Documentation

### Tags

- `{{ NameCol }}`: A column named `NameCol` will be used to fill this placeholder.
- `{{ PrintLayout }}`: A tuple formed by a `QgsLayout` and a `QgsFeature` objects is returned. It must be passed to other filters in order to print a map or return some map attributes like scale, CRS etc.

### Structure

Each document has a complex dictionary with attributes extracted from the relational model centered in the reference layer. You can access all the attributes of the reference layer by calling the attribute name. Other dimenions are stores as dictionaries at the first level of the context dictionary, so:

- Context
  - `global`
  - `layer name`
  - `feature_obj`: QgsFeature object
  - `feature_id`: Feature ID (equivalent of `$id` in QGIS expression)
  - `feature_wkt`: Feature geometry as a well-known text string
  - `feature_geojson`: Feature geometry as GeoJSON string
  - `feature_extent`: QgsRectangle of the feature extent
  - `feature_centroid`: QgsPointXY object of the feature centroid
  - All the attributes of the feature
  - `related layer name`

### Filters

Filters are custom functions designed to extend the capabilities of the DOCX reports. Here is a list of the custom filters implemented by this plugin:

- `exportPrintLayout`: Expects a `PrintLayout` tuple, renders the map and returns a path pointing to the exported PNG figure. Parameters:
  - `figWidth = 1.0`:
  - `isAtlas = True`: Atlas is the mechanism which frames the map to the mapped feature.
  - `outputFolder = None`:
  - `driver = 'png'`: To this date, only PNG is supported. JPG is the next to be implemented
- `renderPictureFromPath`:
- `renderPictureFromBase64`:
- `xForMatch`:
- `multipleCheckBoxes`:

### Further reading

- Although there is a Sphinx API documentation for PyQGIS, QGIS C++ API Reference is preferrable as it reveals the big picture of QGIS classes.
  - [C++ API Reference](https://api.qgis.org/api/index.html)
  - [Python API Reference](https://qgis.org/pyqgis/3.0/)
