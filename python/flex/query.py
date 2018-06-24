""" flex.query

flex.query module contains functions which allows you to compare content
of maya transform nodes used as groups.

:module: flex.query
"""

# imports
from maya import cmds
from flex.decorators import timer  # @UnusedImport


@timer
def get_matching_shapes(source_shapes, target_shapes):
    """ Returns the matching shapes

    This Function will return a dict that contains the target matching shape
    name from the source.

    :param source_shapes: sources dictionary containing prefix-less shapes
    :type group: dict

    :param target: targets dictionary containing prefix-less shapes
    :type group: dict

    :return: The matching target shapes names
    :rtype: dict

    .. note:: This function is the core idea of how Flex finds matching shapes
              from a source group to the target. Because Flex is not part of a
              specific studio pipeline this matching is **shapes name based**.
              Because some studios might bring the source scene into the rig
              scene as a reference or as an import we cover those two cases.

              Using this dict is the fastest way (so far found) to deal with
              a huge amount of names. Finding the matching names on a scene
              with more than 2000 shapes takes 0.0009... seconds.
    """

    # returns matching shapes
    return dict([(source_shapes[s], target_shapes[s])
                 for s in source_shapes
                 if s in target_shapes])


@timer
def get_missing_shapes(source_shapes, target_shapes):
    """ Returns the missing shapes

    This Function will return a dict that contains the missing shape
    found on the target.

    :param source_shapes: sources dictionary containing prefix-less shapes
    :type group: dict

    :param target: targets dictionary containing prefix-less shapes
    :type group: dict

    :return: The missing target shapes names
    :rtype: dict
    """

    # returns matching shapes
    return dict([(source_shapes[s], s)
                 for s in source_shapes
                 if s not in target_shapes])


def get_prefix_less_dict(elements):
    """ Returns a dict containing each element with a stripped prefix

    This Function will return a dict that contains each element resulting on
    the element without the found prefix

    :param elements: List of all your shapes
    :type group: list

    :return: The matching prefix-less elements
    :rtype: dict

    .. note:: Because Flex is not part of a specific studio pipeline we cover
              two different ways to bring the source shapes inside your rig.
              You can either import the source group with the meshes or use
              a Maya reference. This function will strip the prefix whether
              your object is part of a namespace or a double name getting a
              full path naming.
    """

    return dict([(n.split("|")[-1].split(":")[-1], n) for n in elements])


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
        raise RuntimeError('Given element {} does not exists.'.format(group))

    # gets shapes inside the given group
    shapes = cmds.ls(group, dagObjects=True, noIntermediate=True,
                     exactType=('mesh'))

    return shapes or None
