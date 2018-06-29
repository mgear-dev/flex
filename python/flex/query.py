""" flex.query

flex.query module contains functions which allows you to compare content
of maya transform nodes used as groups.

:module: flex.query
"""

# imports
from maya import cmds
from .decorators import timer  # @UnusedImport

def is_valid_group(group):
    """ Checks if group is valid

    Simply checks if the given group exists in the current Maya session and if
    it is a valid transform group.

    :param group: a maya transform node
    :type group: str

    :return: If the group is valid
    :rtype: bool
    """

    if not cmds.objExists(group):
        return False

    if cmds.objectType(group) != 'transform':
        return False

    return True


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


# @timer
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


# @timer
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


# @timer
def get_shapes_from_group(group):
    """ Gets all object shapes existing inside the given group

    :param group: maya transform node
    :type group: str

    :return: list of shapes objects
    :rtype: list str

    .. important:: only mesh shapes are returned for now
    """

    # checks if exists inside maya scene
    if not cmds.objExists(group):
        raise RuntimeError("Given element {} does not exists.".format(group))

    # gets shapes inside the given group
    shapes = cmds.ls(group, dagObjects=True, noIntermediate=True,
                     exactType=("mesh"))

    return shapes or None


# @timer
def get_shape_orig(shape):
    """ Finds the orig (intermediate shape) on the given shape

    :param shape: maya shape node
    :type shape: str

    :return: the found orig shape
    :rtype: str

    .. note:: There are several ways of searching for the orig shape in Maya.
              Here we query it by first getting the given shape history on the
              component type attribute (inMesh, create..) then filtering on
              the result the same shape type. There might be more optimised
              and stable ways of doing this.
    """

    orig_shapes = []
    {orig_shapes.append(n) for n in (cmds.ls(cmds.listHistory(
                                     shape + ".inMesh"),
                                     type="mesh")) if n not in shape}

    if len(orig_shapes) == 0:
        orig_shapes = None

    return orig_shapes


# @timer
def get_transform_selection():
    """ Gets the current dag object selection

    Returns the first selected dag object on a current selection that is a
    transform node

    :return: the first element of the current maya selection
    :rtype: str
    """

    selection = cmds.ls(selection=True, dagObjects=True, type='transform',
                        flatten=True, allPaths=True)

    if len(selection) > 1:
        selection = selection[0]

    return selection or None
