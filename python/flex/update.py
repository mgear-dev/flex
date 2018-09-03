
""" flex.update

flex.update module handles the updating rig process

:module: flex.update
"""

# imports
from __future__ import absolute_import

import logging
from maya import OpenMaya
from maya import cmds
from maya import mel

from mgear.flex.attributes import COMPONENT_DISPLAY_ATTRIBUTES
from mgear.flex.attributes import OBJECT_DISPLAY_ATTRIBUTES
from mgear.flex.attributes import RENDER_STATS_ATTRIBUTES
from mgear.flex.decorators import timer
from mgear.flex.query import get_dependency_node, is_matching_type, \
    is_matching_count
from mgear.flex.query import get_matching_shapes_from_group
from mgear.flex.query import get_missing_shapes_from_group
from mgear.flex.query import get_parent
from mgear.flex.query import get_shape_orig
from mgear.flex.query import get_shape_type_attributes
from mgear.flex.query import is_lock_attribute
from mgear.flex.query import lock_unlock_attribute
import pymel.core as pm

logger = logging.getLogger("mGear: Flex")
logger.setLevel(logging.DEBUG)


def add_attribute(source, target, attribute_name):
    """ Adds the given attribute to the given object

    .. note:: This is a generic method to **addAttr** all type of attributes
              inside Maya. Using the getAddAttrCmd from the MFnAttribute class
              allows avoiding to create one method for each type of attribute
              inside Maya as the addAttr command will differ depending on the
              attribute type and data.

    :param source: the maya source node
    :type source: str

    :param target: the maya target node
    :type target: str

    :param attribute_name: the attribute name to add in the given element
    :type attribute_name: str
    """

    # check if attribute already exists on target
    if cmds.objExists("{}.{}".format(target, attribute_name)):
        return

    # gets the given attribute_name plug attribute
    m_depend_node = get_dependency_node(source)
    m_attribute = m_depend_node.findPlug(attribute_name).attribute()

    # gets the addAttr command from the MFnAttribute function
    fn_attr = OpenMaya.MFnAttribute(m_attribute)
    add_attr_cmd = fn_attr.getAddAttrCmd()[1:-1]

    # creates the attribute on the target
    mel.eval("{} {}".format(add_attr_cmd, target))


def clean_uvs_sets(shape):
    """ Deletes all uv sets besides map1

    This is used to be able to update target shapes with whatever the source
    shape has. This is only relevant for mesh shape types.

    :param shape: The Maya shape node
    :type shape: string
    """

    # check if shape is not a mesh type node
    if cmds.objectType(shape) != "mesh":
        return

    # gets uvs indices
    uvs_idx = cmds.getAttr("{}.uvSet".format(shape), multiIndices=True)

    # deletes the extra indices
    for idx in uvs_idx:
        if idx:
            cmds.setAttr("{}.uvSet[{}]".format(shape, idx), lock=False)
            cmds.removeMultiInstance("{}.uvSet[{}]".format(shape, idx))


def update_attribute(source, target, attribute_name):
    """ Updates the given attribute value

    ..note:: This in a generic method to **setAttr** all type of attributes
             inside Maya. Using the getSetAttrCmds from the MPLug class allows
             avoiding to create one method for each type of attribute inside
             Maya as the setAttr command will differ depending on the
             attribute type and data.

    This method is faster than using PyMel attribute set property.

    :param source: the maya source node
    :type source: str

    :param target: the maya target node
    :type target: str

    :param attribute_name: the attribute name to set in the given target
    :type attribute_name: str
    """

    if not cmds.objExists("{}.{}".format(target, attribute_name)):
        logger.warning("The current target {} does not have attribute: {}"
                       .format(target, attribute_name))
        return

    # checks for locking
    lock = is_lock_attribute(target, attribute_name)

    if not lock_unlock_attribute(target, attribute_name, False):
        logger.error("The given attribute ({}) can't be updated on {}"
                     .format(attribute_name, target))
        return

    # creates pymel nodes to get and apply attributes from
    # I am using pymel as they managed to handle default attributes on
    # referenced nodes correctly. When using MPlug.getSetAttrCmd with kAll
    # this doesn't return the command correctly when nodes in reference have
    # the attribute left as default
    py_source = pm.PyNode(source)
    py_target = pm.PyNode(target)

    # sets the attribute value
    try:
        attr_value = py_source.attr(attribute_name).get()
        py_target.attr(attribute_name).set(attr_value)

    except Exception as e:
        logger.error("The given attribute ({}) can't be updated on {}"
                     .format(attribute_name, target))
        print e
        return

    if lock:
        lock_unlock_attribute(target, attribute_name, True)


def update_deformed_shape(source, target, mismatching_topology=True):
    """ Updates the target shape with the given source shape content

    :param source: maya shape node
    :type source: str

    :param target: maya shape node
    :type target: str
    """

    logger.info("Update deformed shapes options running...")

    # gets orig shape
    deform_origin = get_shape_orig(target)

    if not deform_origin:
        return

    logger.info("Deformed shape found: {}".format(target))

    if not is_matching_type(source, target):
        logger.warning("{} and {} don't have same shape type. passing..."
                       .format(source, target))
        return

    if not mismatching_topology and not is_matching_count(source, target):
        logger.warning("{} and {} don't have same shape vertices count."
                       "passing...".format(source, target))
        return

    deform_origin = deform_origin[0]

    # update the shape
    update_shape(source, deform_origin)


def update_maya_attributes(source, target, attributes):
    """ Updates all maya attributes from the given source to the target

    :param source: maya shape node
    :type source: str

    :param target: maya shape node
    :type target: str

    :param attributes: list of Maya attributes to be updated
    :type attributes: list
    """

    for attribute in attributes:
        update_attribute(source, target, attribute)


def update_plugin_attributes(source, target):
    """ Updates all maya plugin defined attributes

    :param source: maya shape node
    :type source: str

    :param target: maya shape node
    :type target: str
    """

    source_attrs = cmds.listAttr(source, fromPlugin=True)
    taget_attrs = cmds.listAttr(target, fromPlugin=True)

    for attribute in source_attrs:
        if attribute in taget_attrs:
            update_attribute(source, target, attribute)


@timer
def update_rig(source, target, options):
    """ Updates all shapes from the given source group to the target group

    :param source: maya transform node
    :type source: str

    :param target: maya transform node
    :type target: str

    :param options: update options
    :type options: dict
    """

    # gets the matching shapes
    matching_shapes = get_matching_shapes_from_group(source, target)

    logger.info("Matching shapes: {}" .format(matching_shapes))

    for shape in matching_shapes:
        logger.info("Updating: {}".format(matching_shapes[shape]))

        if options["deformed"]:
            update_deformed_shape(shape, matching_shapes[shape],
                                  options["mismatched_topologies"])

        if options["transformed"]:
            update_transformed_shape(shape, matching_shapes[shape],
                                     options["hold_transform_values"])

        if options["user_attributes"]:
            update_user_attributes(shape, matching_shapes[shape])

        if options["object_display"]:
            update_maya_attributes(shape, matching_shapes[shape],
                                   OBJECT_DISPLAY_ATTRIBUTES)

        if options["component_display"]:
            update_maya_attributes(shape, matching_shapes[shape],
                                   COMPONENT_DISPLAY_ATTRIBUTES)

        if options["render_attributes"]:
            update_maya_attributes(shape, matching_shapes[shape],
                                   RENDER_STATS_ATTRIBUTES)

        if options["plugin_attributes"]:
            update_plugin_attributes(shape, matching_shapes[shape])

    logger.info("Source missing shapes: {}" .format(
        get_missing_shapes_from_group(source, target)))
    logger.info("Target missing shapes: {}" .format(
        get_missing_shapes_from_group(target, source)))


def update_shape(source, target):
    """ Connect the shape output from source to the input shape on target

    :param source: maya shape node
    :type source: str

    :param target: maya shape node
    :type target: str
    """

    # clean uvs on mesh nodes
    clean_uvs_sets(target)

    # get attributes names
    attributes = get_shape_type_attributes(source)

    logger.info("Updating shape: {} using --> {}".format(target, source))

    # updates the shape
    cmds.connectAttr("{}.{}".format(source, attributes["output"]),
                     "{}.{}".format(target, attributes["input"]),
                     force=True)

    # forces shape evaluation to achieve the update
    cmds.dgeval("{}.{}".format(target, attributes["output"]))

    # finish shape update
    cmds.disconnectAttr("{}.{}".format(source, attributes["output"]),
                        "{}.{}".format(target, attributes["input"]))


def update_transform(source, target):
    """ Updates the transform node on target

    This method creates a duplicate of the transform node on source and
    uses is as the new parent transform for the target shape

    :param source: maya shape node
    :type source: str

    :param target: maya shape node
    :type target: str
    """

    # create duplicate of the source transform
    holder = cmds.duplicate(source, parentOnly=True,
                            name="mgear_flex_holder")[0]

    # adds the target shape duplicate into the holder transform node
    cmds.parent(target, holder, add=True, shape=True)

    # unlock locked attributes on holder transform node
    for attr in cmds.listAttr(holder, locked=True) or []:
        cmds.setAttr("{}.{}".format(holder, attr), lock=False)

    # updates the shape
    update_shape(source, target)

    # parents new shape under the correct place
    target_parent = get_parent(target)[0]
    target_parent_parent = get_parent(target_parent)[0]
    cmds.parent(holder, target_parent_parent)
    cmds.delete(target_parent)
    cmds.rename(holder, "{}".format(target_parent.split("|")[-1].split(":")
                                    [-1]))


def update_transformed_shape(source, target, hold_transform):
    """ Updates the target shape with the given source shape content

    :param source: maya shape node
    :type source: str

    :param target: maya shape node
    :type target: str

    :param hold_transform: keeps the transform node position values
    :type hold_transform: bool
    """

    logger.info("Update transformed shapes options running...")

    deform_origin = get_shape_orig(target)

    if deform_origin:
        return

    logger.info("Transformed shape found: {}".format(target))

    # maintain transform on target
    if hold_transform:
        update_shape(source, target)

    # update target transform
    else:
        update_transform(source, target)


def update_user_attributes(source, target):
    """ Updates the target shape attributes with the given source shape content

    :param source: maya shape node
    :type source: str

    :param target: maya shape node
    :type target: str

    .. note:: This method loops twice on the use attributes. One time to add
              the missing attributes and the second to set their value. This
              allows avoiding issues when dealing with child attributes.
    """

    # get user defined attributes
    user_attributes = cmds.listAttr(source, userDefined=True) or []

    # loop on user defined attributes if any to ---> addAttr
    for attr in user_attributes:
        # adds attribute on shape
        add_attribute(source, target, attr)

    # loop on user defined attributes if any to ---> setAttr
    for attr in user_attributes:

        # updates the attribute values
        update_attribute(source, target, attr)
