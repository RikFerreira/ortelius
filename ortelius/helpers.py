from qgis.core import *

def qgis_get_layer_type(layer_type):
    # TODO: This method must be replaced by a match-case statement as soon as QGIS 3.34 becomes the LTS
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

def qgis_get_geometry_type(geometry_type):
    # TODO: This method must be replaced by a match-case statement as soon as QGIS 3.34 becomes the LTS
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

def dict_types(ctx):
    out = dict()

    for key in ctx.keys():
        if isinstance(ctx[key], dict):
            types_dict = dict()
            for key_2 in ctx[key].keys():
                types_dict.update(dict_types(ctx[key]))

            out.update({key: types_dict})
        elif isinstance(ctx[key], list):
            types_list = list()
            for item in ctx[key]:
                if isinstance(item, dict):
                    types_dict = dict_types(item)
                    types_list.append(types_dict)
                else:
                    types_list.append(type(item))
            out.update({key: types_list})
        else:
            out.update({key: type(ctx[key])})

    return out
