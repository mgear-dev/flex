""" flex.query

flex.query module contains functions which allows you to compare content
of maya transform nodes used as groups.

:module: flex.query
"""

# imports
from maya import cmds


def get_prefix_from_elem(elem):
    """ Returns a string with the prefix found on the given group

    :param elem: maya transform node
    :type elem: string

    :return: the group prefix
    :rtype: str
    """

    end_name = None

    # namespace case prefix
    if elem.count(':'):
        end_name = elem.split(':')[-1]

    # double name case prefix
    if elem.count('|'):
        end_name = elem.split('|')[-1]

    if end_name:
        return elem.replace(end_name, '')


def get_shapes_from_elem(elem):
    """ Gets all object shapes existing inside the given group

    :param elem: maya transform node
    :type elem: string

    :return: list of shapes objects
    :rtype: list str

    .. important:: only mesh shapes are returned for now
    """

    # checks if exists inside maya scene
    if not cmds.objExists(elem):
        raise RuntimeError('Given element {} does not exists.'.format(elem))

    # gets shapes inside the given group
    shapes = cmds.ls(elem, dagObjects=True, noIntermediate=True,
                     exactType=('mesh'))

    return shapes or None
