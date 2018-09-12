
""" flex.update

flex.update module handles the updating rig process

:module: flex.update
"""

# imports
from __future__ import absolute_import

import functools
from maya import OpenMaya
from maya import cmds
from maya import mel

from mgear.flex import logger
from mgear.flex.attributes import COMPONENT_DISPLAY_ATTRIBUTES
from mgear.flex.attributes import OBJECT_DISPLAY_ATTRIBUTES
from mgear.flex.attributes import RENDER_STATS_ATTRIBUTES
from mgear.flex.decorators import timer
from mgear.flex.query import get_deformers, is_matching_bouding_box
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

    logger.info("Adding {} attribute on {}".format(attribute_name, target))

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

    logger.debug("Cleaning uv sets on {}".format(shape))

    # gets uvs indices
    uvs_idx = cmds.getAttr("{}.uvSet".format(shape), multiIndices=True)

    # deletes the extra indices
    for idx in uvs_idx:
        if idx:
            cmds.setAttr("{}.uvSet[{}]".format(shape, idx), lock=False)
            cmds.removeMultiInstance("{}.uvSet[{}]".format(shape, idx))


def copy_map1_name(source, target):
    """ Copies the name of the uvSet at index zero (map1) to match it

    :param source: maya shape node
    :type source: str

    :param target: maya shape node
    :type target: str
    """

    if not is_matching_type(source, target):
        return

    source_uv_name = cmds.getAttr("{}.uvSet[0].uvSetName".format(source))

    try:
        cmds.setAttr("{}.uvSet[0].uvSetName".format(target), source_uv_name,
                     type="string")
    except RuntimeError:
        logger.debug("{} doesn not have uvs, skipping udpate map1 name".format(
            target))
        return


@timer
def copy_skin_weights(source_skin, target_skin):
    """ Copy skin weights from the given source skin cluster node to the target

    This function is isolated in order to extend research on faster methods
    to transfer skin weights from one node to another.

    :param source_skin: the source skin cluster node name
    :type source_skin: str

    :param target_skin: the target skin cluster node name
    :type target_skin: str
    """

    logger.info("Copying skinning from {} to {}".format(source_skin,
                                                        target_skin))

    cmds.copySkinWeights(sourceSkin=source_skin, destinationSkin=target_skin,
                         surfaceAssociation="closestComponent", noMirror=True,
                         influenceAssociation=("label",
                                               "closestJoint",
                                               "oneToOne"))


@timer
def create_skin_backup(shape, skin_node):
    """ Creates a skinning backup object

    :param shape: the shape node you want to duplicate (should use orig shape)
    :type shape: str

    :param skin_node: the given shape skin cluster node
    :type skin_node: str

    :return: the duplicated shape and the skin cluster node with weights
    :rtype: str, str
    """

    logger.info("Creating skin backup for {}".format(skin_node))

    # gets the skin cluster influences
    influences = cmds.listConnections("{}.matrix".format(skin_node))

    # creates a duplicate mesh of the given shape
    holder_name = "flex_skin_shape_holder"
    shape_holder = cmds.createNode("mesh", name="{}Shape".format(holder_name))
    cmds.rename(shape_holder, "{}".format(shape_holder))
    update_shape(shape, shape_holder)

    # creates new skin cluster node on duplicate
    skin_holder = cmds.skinCluster(influences, shape_holder, bindMethod=0,
                                   obeyMaxInfluences=False, skinMethod=0,
                                   weightDistribution=0, normalizeWeights=1,
                                   removeUnusedInfluence=False, name="{}_SKN"
                                   .format(holder_name))

    # copy the given skin node weights to back up shape
    copy_skin_weights(skin_node, skin_holder[0])

    return "{}".format(shape_holder), "{}".format(skin_holder[0])


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
        logger.warning("The given attribute {} can't be updated on {}"
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
        logger.warning("The given attribute ({}) can't be updated on {}"
                       .format(attribute_name, target))
        return e

    if lock:
        lock_unlock_attribute(target, attribute_name, True)


@timer
def update_deformed_mismatching_shape(source, target, shape_orig):
    """ Updates the target shape with the given source shape content

    :param source: maya shape node
    :type source: str

    :param target: maya shape node
    :type target: str

    :param shape_orig: shape orig on the target shape
    :type shape_orig: str
    """

    logger.debug("Running update deformed mismatched shapes")

    # gets all deformers used the target shape
    deformers = get_deformers(target)

    # THIS PART NEEDS TO BE MOVED
    # return when more than 1 skinCluster node is used on shape
    if len(deformers["skinCluster"]) > 1:
        logger.error("Dual skinning is yet not supported")
        return

    # THIS NEED TO BE REFACTOR
    for deformer_type in deformers:
        for i in deformers[deformer_type] or []:
            cmds.setAttr("{}.envelope".format(i), 0)

    # creates skin backup shape
    shape_backup, skin_backup = create_skin_backup(shape_orig,
                                                   deformers["skinCluster"][0])

    # updates target shape
    cmds.evalDeferred(functools.partial(update_shape, source, shape_orig))

    # copy skinning from backup
    cmds.evalDeferred(functools.partial(copy_skin_weights, skin_backup,
                                        deformers["skinCluster"][0]))

    # deletes the holder
    cmds.evalDeferred(functools.partial(cmds.delete, cmds.listRelatives(
        shape_backup, parent=True)))

    # updates uv sets on target shape
    cmds.evalDeferred(functools.partial(update_uvs_sets, target))

    # refreshes view
    cmds.refresh()


def update_deformed_shape(source, target, mismatching_topology=True):
    """ Updates the target shape with the given source shape content

    :param source: maya shape node
    :type source: str

    :param target: maya shape node
    :type target: str

    :param mismatching_topology: ignore or not mismatching topologies
    :type mismatching_topology: bool
    """

    # gets orig shape
    deform_origin = get_shape_orig(target)

    # returns as target is not a deformed shape
    if not deform_origin:
        return

    logger.debug("Deformed shape found: {}".format(target))

    # returns if source and target shapes don't match
    if not is_matching_type(source, target):
        logger.warning("{} and {} don't have same shape type. passing..."
                       .format(source, target))
        return

    # returns if vertices count isn't equal and mismatching isn't requested
    if not mismatching_topology and not is_matching_count(source, target):
        logger.warning("{} and {} don't have same shape vertices count."
                       "passing...".format(source, target))
        return

    deform_origin = deform_origin[0]

    # updates map1 name
    copy_map1_name(source, deform_origin)

    # updates on mismatching topology but same bounding box
    if mismatching_topology and not is_matching_count(source, target) and (
            is_matching_bouding_box(source, target)):
        update_deformed_mismatching_shape(source, target, deform_origin)
        return

    # update the shape
    update_shape(source, deform_origin)

    # update uvs set on target
    update_uvs_sets(target)


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

    source_attrs = cmds.listAttr(source, fromPlugin=True) or []
    taget_attrs = cmds.listAttr(target, fromPlugin=True) or []

    logger.debug("Updating  plugin attributes on {}".format(target))
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

    logger.info("-" * 90)
    logger.info("Matching shapes: {}" .format(matching_shapes))
    logger.info("-" * 90)

    for shape in matching_shapes:
        logger.debug("-" * 90)
        logger.debug("Updating: {}".format(matching_shapes[shape]))

        if options["deformed"]:
            update_deformed_shape(shape, matching_shapes[shape],
                                  options["mismatched_topologies"])

        if options["transformed"]:
            update_transformed_shape(shape, matching_shapes[shape],
                                     options["hold_transform_values"])

        if options["user_attributes"]:
            update_user_attributes(shape, matching_shapes[shape])

        if options["object_display"]:
            logger.debug("Updating object display attributes on {}"
                         .format(matching_shapes[shape]))
            update_maya_attributes(shape, matching_shapes[shape],
                                   OBJECT_DISPLAY_ATTRIBUTES)

        if options["component_display"]:
            logger.debug("Updating component display attributes on {}"
                         .format(matching_shapes[shape]))
            update_maya_attributes(shape, matching_shapes[shape],
                                   COMPONENT_DISPLAY_ATTRIBUTES)

        if options["render_attributes"]:
            logger.debug("Updating render attributes on {}"
                         .format(matching_shapes[shape]))
            update_maya_attributes(shape, matching_shapes[shape],
                                   RENDER_STATS_ATTRIBUTES)

        if options["plugin_attributes"]:
            update_plugin_attributes(shape, matching_shapes[shape])

    logger.info("-" * 90)
    logger.info("Source missing shapes: {}" .format(
        get_missing_shapes_from_group(source, target)))
    logger.info("Target missing shapes: {}" .format(
        get_missing_shapes_from_group(target, source)))
    logger.info("-" * 90)


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

    logger.debug("Updating shape: {} using --> {}".format(target, source))

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

    logger.debug("Updating transform node on {} from {}".format(target,
                                                                source))

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

    deform_origin = get_shape_orig(target)

    if deform_origin:
        return

    logger.debug("Transformed shape found: {}".format(target))

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
    user_attributes = cmds.listAttr(source, userDefined=True)

    if not user_attributes:
        return

    logger.debug("Updating user attributes on {}".format(target))

    # loop on user defined attributes if any to ---> addAttr
    for attr in user_attributes:
        # adds attribute on shape
        add_attribute(source, target, attr)

    # loop on user defined attributes if any to ---> setAttr
    for attr in user_attributes:
        # updates the attribute values
        update_attribute(source, target, attr)


def update_uvs_sets(shape):
    """ Forces a given mesh shape uvs to update
    """

    if cmds.objectType(shape) != "mesh":
        return

    # forces uv refresh
    cmds.setAttr("{}.outForceNodeUVUpdate ".format(shape), True)
