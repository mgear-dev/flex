
""" flex.update

flex.update module handles the updating rig process

:module: flex.update
"""

# imports
from __future__ import absolute_import

from maya import OpenMaya
from maya import cmds
from maya import mel

from mgear.flex import logger
from mgear.flex.attributes import BLENDSHAPE_TARGET
from mgear.flex.attributes import COMPONENT_DISPLAY_ATTRIBUTES
from mgear.flex.attributes import OBJECT_DISPLAY_ATTRIBUTES
from mgear.flex.attributes import RENDER_STATS_ATTRIBUTES
from mgear.flex.decorators import timer
from mgear.flex.query import filter_shape_orig
from mgear.flex.query import get_deformers, is_matching_bouding_box
from mgear.flex.query import get_dependency_node, is_matching_type, \
    is_matching_count
from mgear.flex.query import get_matching_shapes_from_group
from mgear.flex.query import get_missing_shapes_from_group
from mgear.flex.query import get_parent
from mgear.flex.query import get_prefix_less_name
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


def copy_blendshape_node(node, target):
    """ Copies the given blendshape node into the given target shape

    :param node: blendshape node
    :type node: str

    :param target: target shape node
    :type target: str

    :return: copied blenshape node
    :rtype: str
    """

    logger.debug("Copying blendshape node {} to {}".format(node, target))

    # get blendshape targets indices
    targets_idx = cmds.getAttr("{}.weight".format(node), multiIndices=True)

    # skip node if no targets where found
    if not targets_idx:
        return

    # list for ignored targets (when they are live connected)
    ignore = []

    # creates blendshape deformer node on target
    node_copy = cmds.deformer(target, type="blendShape", name="flex_copy_{}"
                              .format(node))[0]

    # loop on blendshape targets indices
    for idx in targets_idx:
        # input target group attribute
        attr_name = (BLENDSHAPE_TARGET.format(node, idx))

        # blendshape target name
        target_name = cmds.aliasAttr("{}.weight[{}]".format(node, idx),
                                     query=True)

        # loop on actual targets and in-between targets
        for target in cmds.getAttr(attr_name, multiIndices=True):
            # target attribute name
            target_attr = "{}[{}]".format(attr_name, target)

            # checks for incoming connections on the geometry target
            if cmds.listConnections("{}.inputGeomTarget".format(target_attr),
                                    destination=False):

                logger.warning("{} can't be updated because it is a live "
                               "target".format(target_name))
                ignore.append(idx)
                continue

            # updates node copy target
            destination = target_attr.replace(target_attr.split(".")[0],
                                              node_copy)
            cmds.connectAttr(target_attr, destination, force=True)
            cmds.disconnectAttr(target_attr, destination)

        # skips updating target name if this was a life target
        if idx in ignore:
            continue

        # forces the weight attribute to be shown on the blendshape node
        cmds.setAttr("{}.weight[{}]".format(node_copy, idx), 0)

        # updates blendshape node attribute name
        if target_name:
            cmds.aliasAttr(target_name, "{}.weight[{}]"
                           .format(node_copy, idx))

    # gets targets on copied node to see if there is any node with zero target
    idx = cmds.getAttr("{}.weight".format(node_copy), multiIndices=True)
    if not idx:
        cmds.delete(node_copy)
        return

    return node_copy


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

    # copy skin command
    cmds.copySkinWeights(sourceSkin=source_skin, destinationSkin=target_skin,
                         surfaceAssociation="closestComponent", noMirror=True,
                         influenceAssociation=("label",
                                               "closestJoint",
                                               "oneToOne"))
    # forces a refresh in order to correctly evaluate the skin node
    # doing a dgeval or dgdirty did not created enough stable results are
    # forcing the refresh
    cmds.refresh()


@timer
def create_blendshapes_backup(source, target, nodes):
    """ Creates an updated backup for the given blendshapes nodes on source

    .. important:: This method does not work as the other source/target type
                   of methods in flex. The source is the current geometry
                   before topology update containing the blendshape nodes.
                   We use it in order to create a wrap to the newer target
                   geometry topology.

    :param source: current shape node
    :type source: str

    :param target: new shape node
    :type target: str

    :return: a shape node containing the new blenshape targets
    :rtype: str
    """

    logger.debug("Creating blendshapes backup")

    # gets simpler shape name
    shape_name = get_prefix_less_name(target)

    # get attributes types
    attrs = get_shape_type_attributes(target)

    # creates source duplicate
    intermediate = get_shape_orig(source)[0]
    source_duplicate = create_duplicate(intermediate, "{}_flex_bs_sourceShape"
                                        .format(shape_name))

    # first loops to create a clean copy of the blendshape nodes
    nodes_copy = []
    for node in nodes:
        duplicate = copy_blendshape_node(node, source_duplicate)
        if duplicate:
            nodes_copy.append(duplicate)

    # creates warped target shape
    warp_target = create_duplicate(target, "{}_flex_bs_warpShape"
                                   .format(shape_name))

    # wraps the duplicate to the source
    create_wrap(source_duplicate, warp_target)

    # creates blendshape target shape
    target_duplicate = create_duplicate(target, "{}_flex_bs_targetShape"
                                        .format(shape_name))

    return_nodes = []

    # loops on the blendshape nodes
    for node in nodes_copy:
        # creates transfer blendshape
        transfer_node = cmds.deformer(target_duplicate, type="blendShape",
                                      name="flex_transfer_{}".format(node))[0]

        # get blendshape targets indices. We skip verification because at this
        # stage the copied blendshapes nodes will always have targets
        targets_idx = cmds.getAttr("{}.weight".format(node), multiIndices=True)

        # loop on blendshape targets indices
        for idx in targets_idx or []:
            # input target group attribute
            attr_name = (BLENDSHAPE_TARGET.format(node, idx))

            # blendshape target name
            target_name = cmds.aliasAttr("{}.weight[{}]".format(node, idx),
                                         query=True)

            # loop on actual targets and in-between targets
            for target in cmds.getAttr(attr_name, multiIndices=True):

                # gets and sets the blendshape weight value
                weight = float((target - 5000) / 1000.0)
                cmds.setAttr("{}.weight[{}]".format(node, idx), weight)

                # geometry target attribute
                geometry_target_attr = "{}[{}].inputGeomTarget".format(
                    attr_name, target)

                shape_target = geometry_target_attr.replace(
                    geometry_target_attr.split(".")[0], transfer_node)

                # updates the target
                cmds.connectAttr("{}.{}".format(warp_target, attrs["output"]),
                                 shape_target, force=True)

                cmds.disconnectAttr("{}.{}"
                                    .format(warp_target, attrs["output"]),
                                    shape_target)

                cmds.setAttr("{}.weight[{}]".format(node, idx), 0)

            cmds.setAttr("{}.weight[{}]".format(transfer_node, idx), 0)

            if target_name:
                cmds.aliasAttr(target_name, "{}.weight[{}]".format(
                    transfer_node, idx))

        # adds blendshape node to nodes to return
        return_nodes.append(transfer_node)

    # deletes backup process shapes
    cmds.delete(cmds.listRelatives(source_duplicate, parent=True),
                cmds.listRelatives(warp_target, parent=True))

    return return_nodes, target_duplicate


def create_duplicate(shape, duplicate_name):
    """ Creates a shape node duplicate

    :param shape: the shape node to duplicate
    :type shape: str

    :param name: the name for the duplicate
    :type name: str

    :return: the duplicated shape node
    :rtype: str
    """

    logger.debug("Creating shape duplicate for {}".format(shape))
    shape_holder = cmds.createNode(cmds.objectType(shape),
                                   name="{}Shape".format(duplicate_name))
    cmds.rename(shape_holder, "{}".format(shape_holder))
    update_shape(shape, shape_holder)

    return shape_holder


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

    # creates a duplicate shape of the given shape
    holder_name = "{}_flex_skin_shape_holder".format(
        get_prefix_less_name(shape))
    shape_duplicate = create_duplicate(shape, holder_name)

    # creates new skin cluster node on duplicate
    skin_holder = cmds.skinCluster(influences, shape_duplicate, bindMethod=0,
                                   obeyMaxInfluences=False, skinMethod=0,
                                   weightDistribution=0, normalizeWeights=1,
                                   removeUnusedInfluence=False, name="{}_SKN"
                                   .format(holder_name))

    # copy the given skin node weights to back up shape
    copy_skin_weights(skin_node, skin_holder[0])

    return "{}".format(shape_duplicate), "{}".format(skin_holder[0])


def create_wrap(source, target, intermediate=None):
    """ Creates a wrap deformer on the target by using source as driver

    :param source: the maya source node
    :type source: str

    :param target: the maya target node
    :type target: str

    :param intermediate: the intermediate shape to use on the warp node
    :type intermediate: str

    :return: wrap node
    :rtype: str
    """

    logger.debug("Creating wrap deformer for {} using {}".format(target,
                                                                 source))

    # creates the deformer
    target_type = cmds.objectType(target)
    wrap_node = cmds.deformer(target, type="wrap", name="flex_warp")[0]
    cmds.setAttr("{}.exclusiveBind".format(wrap_node), 1)
    cmds.setAttr("{}.autoWeightThreshold".format(wrap_node), 1)
    cmds.setAttr("{}.dropoff[0]".format(wrap_node), 4.0)

    # sets settings for nurbs type shapes
    if target_type == "nurbsSurface" or target_type == "nurbsCurve":
        cmds.setAttr("{}.nurbsSamples[0]".format(wrap_node), 10)
    # sets settings for mesh type shapes
    else:
        cmds.setAttr("{}.inflType[0]".format(wrap_node), 2)

    # gets attributes types for the given target
    attrs = get_shape_type_attributes(target)

    # filters intermediate shape
    intermediate_shape = filter_shape_orig(source, intermediate)

    # connects the wrap node to the source
    cmds.connectAttr("{}.{}".format(intermediate_shape, attrs["output_world"]),
                     "{}.basePoints[0]".format(wrap_node), force=True)
    cmds.connectAttr("{}.{}".format(source, attrs["output"]),
                     "{}.driverPoints[0]".format(wrap_node), force=True)
    cmds.connectAttr("{}.worldMatrix[0]".format(target),
                     "{}.geomMatrix".format(wrap_node), force=True)

    return wrap_node


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


def update_blendshapes_nodes(source_nodes, target_nodes):
    """ Update all target shapes with the given source shapes

    :param source_nodes: source blendshape nodes
    :type source_nodes: list(str)

    :param target_nodes: target blendshape nodes
    :type target_nodes: list(str)
    """

    for node in target_nodes:
        match_node = [x for x in source_nodes if node in x] or None

        if not match_node:
            continue

        # gets source and targets indices
        targets_idx = cmds.getAttr("{}.weight".format(node), multiIndices=True)
        source_idx = cmds.getAttr("{}.weight".format(match_node[0]),
                                  multiIndices=True)

        for idx in targets_idx:
            # blendshape target name
            target_name = cmds.aliasAttr("{}.weight[{}]".format(node, idx),
                                         query=True)

            # gets corresponding source idx
            match_idx = [x for x in source_idx if cmds.aliasAttr(
                "{}.weight[{}]".format(match_node[0], x),
                query=True) == target_name]

            if not match_idx:
                continue

            # input target group attribute
            source_name = (BLENDSHAPE_TARGET.format(match_node[0],
                                                    match_idx[0]))
            target_name = (BLENDSHAPE_TARGET.format(node, idx))

            # loop on actual targets and in-between targets
            for target in cmds.getAttr(target_name, multiIndices=True):
                # target attribute name
                source_attr = "{}[{}]".format(source_name, target)
                target_attr = "{}[{}]".format(target_name, target)

                cmds.connectAttr(source_attr, target_attr, force=True)
                cmds.disconnectAttr(source_attr, target_attr)


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

#     # Turns all deformers envelope off
#     for deformer_type in deformers:
#         for i in deformers[deformer_type] or []:
#             try:
#                 cmds.setAttr("{}.envelope".format(i), 0)
#             except RuntimeError:
#                 mute_node = cmds.mute("{}.envelope".format(i), force=True)[0]
#                 cmds.setAttr("{}.hold".format(mute_node), 0)

    # creates blendshapes nodes backup
    bs_nodes = None
    if len(deformers["blendShape"]):
        bs_nodes, bs_shape = create_blendshapes_backup(target, source,
                                                       deformers["blendShape"])

    # creates skin backup shape
    shape_backup, skin_backup = create_skin_backup(shape_orig,
                                                   deformers["skinCluster"][0])

    # updates target shape
    update_shape(source, shape_orig)

    # copy skinning from backup
    copy_skin_weights(skin_backup, deformers["skinCluster"][0])

    # deletes the holder
    cmds.delete(cmds.listRelatives(shape_backup, parent=True))

    if bs_nodes:
        update_blendshapes_nodes(bs_nodes, deformers["blendShape"])

    cmds.delete(cmds.listRelatives(bs_shape, parent=True))

    # updates uv sets on target shape
    update_uvs_sets(target)


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
