# -*- coding: utf-8 -*-

from qgis.core import *
from qgis.utils import iface

from PyQt5.QtCore import QDateTime, QDate, QTime, QByteArray

import json
import datetime

class QgisContext:
    def __init__(self, iface, project):
        self.iface = iface
        self.project_instance = project

        self.relations = self.project_instance.relationManager().relations()

        self.__context = dict()

        self.__tree_root_layer = ''
        self.__tree_root_index_feature = ''
        self.__tree_depth = 0
        self.__tree_layers = 0
        self.__tree_features = 0

        pass

    def __repr__(self) -> str:
        return (
            'Qgis context dictionary for jinja2 rendering.\n'
            f'Root layer: {self.__tree_root_layer}\n'
            f'Root feature index: {self.__tree_root_index_feature}\n'
            f'Depth of the tree: {self.__tree_depth}\n'
            f'Layers in the tree: {self.__tree_layers}\n'
            f'Features in the tree: {self.__tree_features}\n'
        )

    def __mount_global_dict(self) -> dict:
        env_global = {
            'global': {
                'project_obj': self.project_instance,
                'mapCanvas': self.iface.mapCanvas(),
                'project_bbox': [
                    self.iface.mapCanvas().extent().xMinimum(),
                    self.iface.mapCanvas().extent().yMinimum(),
                    self.iface.mapCanvas().extent().xMaximum(),
                    self.iface.mapCanvas().extent().yMaximum()
                ],
                'global_vars': {x: QgsExpressionContextUtils.globalScope().variable(x) for x in QgsExpressionContextUtils.globalScope().variableNames()},
                'project_vars': {x: QgsExpressionContextUtils.projectScope(self.project_instance).variable(x) for x in QgsExpressionContextUtils.projectScope(self.project_instance).variableNames()}
            }
        }

        return env_global

    def __mount_layer_dict(self, layer) -> dict:
        if not isinstance(layer, qgis.core.QgsVectorLayer):
            raise TypeError("Reference layer is not a QgsVectorLayer object!")

        env_layer = {
            'layer': {
                'layer_obj': layer,
                'layer_type': get_layer_type(layer.type()),
                'layer_geometry_type': get_geometry_type(layer.geometryType()),
                'layer_name': layer.name(),
                'layer_id': layer.id(),
                'layer_source': layer.sourceName(),
                'layer_extent': layer.extent(),
                'layer_bbox': [
                    layer.extent().xMinimum(),
                    layer.extent().yMinimum(),
                    layer.extent().xMaximum(),
                    layer.extent().yMaximum()
                ]
            }
        }

        return env_layer

    def __mount_feature_dict(self, layer, feature) -> dict:
        if not isinstance(feature, qgis.core.QgsFeature):
            raise TypeError("Current feature is not a QgsFeature object!")

        env_feature = dict()

        env_feature.update(self.__mount_layer_dict(layer))

        env_feature.update({
            'feature': {
                'feature_obj': feature,
                'feature_id': feature.id(),
                'feature_wkt': feature.geometry().asWkt() if layer.isSpatial() and not feature.geometry().isNull() else None,
                'feature_geojson': feature.geometry().asJson() if layer.isSpatial() and not feature.geometry().isNull() else None,
                'feature_extent': feature.geometry().boundingBox() if layer.isSpatial() and not feature.geometry().isNull() else None,
                'feature_centroid': feature.geometry().centroid().asPoint() if layer.isSpatial() and not feature.geometry().isNull() else None
            }
        })

        attr_dict = {
            'attributes': dict()
        }
        if layer.type() == QgsMapLayerType.VectorLayer:
            for field in layer.fields().toList():
                value = feature[field.name()]

                if isinstance(value, QDateTime):
                    value = value.toString('yyyy/MM/dd HH:mm:ss.zzz')
                    value = datetime.datetime.strptime(value, '%Y/%m/%d %H:%M:%S.%f')

                if isinstance(value, QDate):
                    value = value.toString('yyyy/MM/dd')
                    value = datetime.datetime.strptime(value, '%Y/%m/%d')

                if isinstance(value, QTime):
                    value = value.toString('HH:mm:ss.zzz')
                    value = datetime.datetime.strptime(value, '%H:%M:%S.%f')

                if isinstance(value, QByteArray):
                    value = value.toBase64().data()

                attr_dict['attributes'][field.name()] = value

        env_feature['feature'].update(attr_dict)

        if self.relations.values():
            env_feature['relations'] = dict()

        for relation in self.relations.values():
            related_features = list(relation.getRelatedFeatures(feature))
            related_layer = relation.referencingLayer()

            if len(related_features) == 0:
                continue

            relation_list = list()
            for rel_feat in related_features:
                relation_list.append(self.__mount_feature_dict(related_layer, rel_feat))

            rel_dict = {related_layer.name(): relation_list}

            env_feature['relations'].update(rel_dict)

        return env_feature

    def __mount_layouts_dict(self) -> dict:
        self.layout_manager = self.project_instance.layoutManager()

        env_layouts = {
            'layouts': dict()
        }

        for layout in self.layout_manager.printLayouts():
            env_layouts['layouts'].update({layout.name(): {'layout_obj': layout, 'layout_atlas': layout.atlas()}})

        return env_layouts

    def mount(self, layer, feature) -> None:
        self.__tree_root_layer = layer.name()
        self.__tree_root_index_feature = str(feature.id())
        self.__tree_depth = 0
        self.__tree_layers = 0
        self.__tree_features = 0

        self.__context = dict()

        self.__context.update(self.__mount_global_dict())
        self.__context.update(self.__mount_feature_dict(layer, feature))
        self.__context.update(self.__mount_layouts_dict())

        self.__set_tree_stats(self.__context)

    def __set_tree_stats(self, ctx, count = 0) -> None:
        if count == 0:
            count += 1

            for key in ctx['relations'].keys():
                self.__set_tree_stats(ctx['relations'][key], count)

            self.__tree_features += 1
        else:
            count += 1

            for item in ctx:
                for key in item['relations'].keys():
                    self.__set_tree_stats(item['relations'][key], count)

            self.__tree_features += len(ctx)

        if self.__tree_depth < count:
            self.__tree_depth = count

        self.__tree_layers += 1

    def get_dict(self) -> dict:
        return self.__context

    def get_json(self) -> str:
        return json.dumps(self.__context, indent = 4, default = str)


def get_layer_type(layer_type):
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

def get_geometry_type(geometry_type):
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

'''
con = QgisContext(iface, QgsProject.instance())
layer = iface.activeLayer()
feature = [x for x in layer.getSelectedFeatures()][0]
con.mount(layer, feature)
pyperclip.copy(con.get_json())
'''

if __name__ == '__console__':
    con = QgisContext(iface, QgsProject.instance())
    layer = iface.activeLayer()
    feature = [x for x in layer.getSelectedFeatures()][0]
    con.mount(layer, feature)
    pyperclip.copy(con.get_json())

    print(con)
