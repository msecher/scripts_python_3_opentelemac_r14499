#!/usr/bin/env python3
""" Handling shapefile to extract polygon """

from utils.exceptions import TelemacException

def read_shape_data(shape_file, get_names=False):
    """
    Extract a polygon from a shape file

    @param shape_file (string) Name of the shape file

    @return (list) The list representing the polygon (list of 2-uple)
    """
    import data_manip.formats.shapefile as shapefile
    from os import path
    if get_names:
        root, _ = path.splitext(shape_file)
        shape = shapefile.Reader(shape_file, dbf=root+'.dbf')
    else:
        shape = shapefile.Reader(shape_file)

    if get_names:
        names = []
        for record in shape.iterRecords():
            names.append(record[1])

        return names
    else:
        res = []
        #first feature of the shapefile
        for feature in shape.shapeRecords():
            first = feature.shape.__geo_interface__
            if first['type'] not in [("LineString"), ("Polygon"), ("Point")]:
                raise TelemacException(\
                        "No linestring or Polygon or Point in shapefile\n"\
                        "type: {} not handled".format(first['type']))

            if first['type'] == ("LineString"):
                res.append(list(first['coordinates']))
            elif first['type'] == ("Polygon"):
                res.append(list(first['coordinates'][0][:-1]))
            elif first['type'] == ("Point"):
                res.append(list(first['coordinates']))
        return res
