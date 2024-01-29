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

### Filters

- `exportPrintLayout`: Expects a `PrintLayout` tuple, renders the map and returns a path pointing to the exported PNG figure. Parameters:
  - `figWidth = 1.0`:
  - `isAtlas = True`: Atlas is the mechanism which frames the map to the mapped feature.
  - `outputFolder = None`:
  - `driver = 'png'`: To this date, only PNG is supported. JPG is the next to be implemented
- `renderPictureFromPath`:
- `renderPictureFromBase64`:
- `xForMatch`:
- `multipleCheckBoxes`:
