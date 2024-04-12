from qgis.core import *

def qgis_get_layer_type(layer_type) -> str:
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

def qgis_get_geometry_type(geometry_type) -> str:
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

def dict_types(ctx) -> dict:
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

def qgis_qttypes_to_python(value):
    output = float('inf')

    if isinstance(value, QDateTime):
        output = value.toString('yyyy/MM/dd HH:mm:ss.zzz')
        output = datetime.datetime.strptime(value, '%Y/%m/%d %H:%M:%S.%f')

    if isinstance(value, QDate):
        output = value.toString('yyyy/MM/dd')
        output = datetime.datetime.strptime(value, '%Y/%m/%d')

    if isinstance(value, QTime):
        output = value.toString('HH:mm:ss.zzz')
        output = datetime.datetime.strptime(value, '%H:%M:%S.%f')

    if isinstance(value, QByteArray):
        output = value.toBase64().data()

    if isinstance(value, QVariant) and value.value() == None:
        output = None

    if value.__class__.__module__ == 'builtins':
        output = value

    if output == float('inf'):
        raise TypeError(f'The object provided is not a built-in type or any of the recognized PyQt5 types. Check for support to {type(value)}.')

    return output
