""" flex.query

flex.query module contains functions which allows you to compare content
of maya transform nodes used as groups.

:module: flex.query
"""

# import
from __future__ import absolute_import
from maya import OpenMaya
from maya import cmds
import os
from mgear.flex.decorators import timer  # @UnusedImport


# flex imports
def get_dependency_node(element):
    """ Returns a Maya MFnDependencyNode from the given element

    :param element: Maya node to return a dependency node class object
    :type element: string

    :return: the element in a Maya MFnDependencyNode object
    :rtype: MFnDependencyNode
    """

    # adds the elements into an maya selection list
    m_selectin_list = OpenMaya.MSelectionList()
    m_selectin_list.add(element)

    # creates an MObject
    m_object = OpenMaya.MObject()

    # gets the MObject from the list
    m_selectin_list.getDependNode(0, m_object)

    return OpenMaya.MFnDependencyNode(m_object)


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


def get_parent(element):
    """ Returns the first parent found for the given element

    :param element: A Maya dag node
    :type shape: string
    """

    return cmds.listRelatives(element, parent=True, fullPath=True,
                              type="transform")


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


def get_resources_path():
    """ Gets the directory path to the resources files
    """

    file_dir = os.path.dirname(__file__)

    if "\\" in file_dir:
        file_dir = file_dir.replace("\\", "/")

    return "{}/resources".format(file_dir)


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

    # gets attributes names
    attributes = get_shape_type_attributes(shape)

    orig_shapes = []
    {orig_shapes.append(n) for n in (cmds.ls(cmds.listHistory(
        "{}.{}".format(shape, attributes["input"])),
        type=cmds.objectType(shape))) if n != shape}

    if len(orig_shapes) == 0:
        orig_shapes = None

    return orig_shapes


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

    shapes = []

    # gets shapes inside the given group
    shapes.extend(cmds.ls(group, dagObjects=True, noIntermediate=True,
                     exactType=("mesh")) or [])

    shapes.extend(cmds.ls(group, dagObjects=True, noIntermediate=True,
                          exactType=("nurbsCurve")) or [])

    shapes.extend(cmds.ls(group, dagObjects=True, noIntermediate=True,
                          exactType=("nurbsSurface"))or [])

    if not shapes:
        raise ValueError("No shape(s) found under the given group: '{}'"
                         .format(group))

    return shapes


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

    if len(selection) >= 1:
        selection = selection[0]

    return selection or None


def get_shape_type_attributes(shape):
    """ Returns a dict with the attributes names depending on the shape type

    This function returns the points, output, input and axes attributes for
    the corresponding shape type. Mesh type of nodes will be set as default
    but nurbs surfaces and nurbs curves are supported too.

    on mesh nodes: points = pnts
                   output = outMesh
                   input = inMesh
                   p_axes = (pntx, pnty, pntz)

    on nurbs nodes: points = controlPoints
                    output = local
                    input = create
                    p_axes = (xValue, yValue, zValue)

    :param shape: maya shape node
    :type shape: str

    :return: corresponding attributes names
    :rtype: dict
    """

    # declares the dict
    shape_attributes = dict()

    # set the default values for a mesh node type
    shape_attributes["points"] = "pnts"
    shape_attributes["input"] = "inMesh"
    shape_attributes["output"] = "outMesh"
    shape_attributes["p_axes"] = ("pntx", "pnty", "pntz")

    if cmds.objectType(shape) == "nurbsSurface" or (cmds.objectType(shape) ==
                                                    "nurbsCurve"):

        # set the default values for a nurbs node type
        shape_attributes["points"] = "controlPoints"
        shape_attributes["input"] = "create"
        shape_attributes["output"] = "local"
        shape_attributes["p_axes"] = ("xValue", "yValue", "zValue")

    return shape_attributes


def is_lock_attribute(element, attribute):
    """ Returns if the given attribute on the element is locked

    :param element: Maya node name
    :type element: string

    :param attribute: Maya attribute name. Must exist
    :type attribute: string

    :return: if attribute is locked
    :rtype: bool
    """

    return cmds.getAttr("{}.{}".format(element, attribute), lock=True)


def is_maya_batch():
    """ Returns if the current session is a Maya batch session or not

    :return: if Maya is on batch mode or not
    :rtype: bool
    """

    return cmds.about(batch=True)


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


def lock_unlock_attribute(element, attribute, state):
    """ Unlocks the given attribute on the given element

    :param element: Maya node name
    :type element: string

    :param attribute: Maya attribute name. Must exist
    :type attribute: string

    :param state: If we should lock or unlock
    :type state: bool

    :return: If the setting was successful or not
    :rtype: bool
    """

    try:
        cmds.setAttr("{}.{}".format(element, attribute), lock=state)
        return True
    except RuntimeError:
        return False
