""" flex.compare

flex.compare module contains functions which allows you to compare content
of maya transform nodes used as groups.

:module: flex.compare
"""

# imports
from maya import cmds


def get_prefix_from_group(group):
    """ Returns a string with the prefix found on the given group

    :param group: maya transform node
    :type group: string

    :return: the group prefix
    :rtype: str
    """

    if not group.count(':'):
        return None

    end_name = group.split(':')[-1]
    return group.replace(end_name, '')


def get_shapes_from_group(group):
    """ Gets all object shapes existing inside the given group

    :param group: maya transform node
    :type group: string

    :return: list of shapes objects
    :rtype: list str

    .. important:: only mesh shapes are returned for now
    """

    # checks if exists inside maya scene
    if not cmds.objExists(group):
        return None

    # gets shapes inside the given group
    shapes = cmds.ls(group, dagObjects=True, noIntermediate=True,
                     exactType=('mesh'))

    return shapes or None


def get_updatable_shapes(source, target):
    """ Returns a list of shapes that can be updated on the target group
    """

    source_shapes = get_shapes_from_group(source)
    target_shapes = get_shapes_from_group(target)

    result = []

    for shape in source_shapes:

        prefix = get_prefix_from_group(source)
        target_name = shape.replace(prefix, '')

        if target_name not in target_shapes:
            continue
        result.append(shape)

    return result
