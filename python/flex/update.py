
""" flex.update

flex.update module handles the updating rig process

:module: flex.update
"""

# imports
import logging
from maya import cmds
from .decorators import timer
from .query import (get_matching_shapes, get_shapes_from_group,
                    get_prefix_less_dict, get_missing_shapes,
                    get_shape_orig)

logger = logging.getLogger("mGear: Flex")
logger.setLevel(logging.DEBUG)


@timer
def update_rig(source, target):
    """ Updates all shapes from the given source group to the target group

    :param source: maya transform node
    :type group: str

    :param target: maya transform node
    :type group: str
    """

    # gets all shapes on source and target
    source_shapes = get_shapes_from_group(source)
    target_shapes = get_shapes_from_group(target)

    # gets prefix-less shapes
    sources_dict = get_prefix_less_dict(source_shapes)
    targets_dict = get_prefix_less_dict(target_shapes)

    # gets the matching shapes
    matching_shapes = get_matching_shapes(sources_dict, targets_dict)

    # gets missing target shapes
    missing_target_shapes = get_missing_shapes(sources_dict, targets_dict)

    # gets missing source shapes
    missing_source_shapes = get_missing_shapes(targets_dict, sources_dict)

    logger.info("Matching shapes: {}" .format(matching_shapes))

    for shape in matching_shapes:
        logger.info("Updating: {}".format(shape))
        update_shape(shape, matching_shapes[shape])
        update_shape_user_attributes(shape, matching_shapes[shape])

    logger.info("Source missing shapes: {}" .format(missing_source_shapes))
    logger.info("Target missing shapes: {}" .format(missing_target_shapes))


def update_shape(source_shape, target_shape):
    """ Updates the target shape with the given source shape content

    :param source_shape: maya shape node
    :type source_shape: str

    :param target_shape: maya shape node
    :type target_shape: str
    """

    deform_origin = get_shape_orig(target_shape)

    if not deform_origin:
        return

    deform_origin = deform_origin[0]

    # updates the shape
    cmds.connectAttr("{}.outMesh".format(source_shape),
                     "{}.inMesh".format(deform_origin), force=True)

    # forces shape evaluation to achieve the update
    cmds.dgeval("{}.outMesh".format(target_shape))

    # finish shape update
    cmds.disconnectAttr("{}.outMesh".format(source_shape),
                        "{}.inMesh".format(deform_origin))


def update_shape_user_attributes(source_shape, target_shape):
    """ Updates the target shape attributes with the given source shape content

    :param source_shape: maya shape node
    :type source_shape: str

    :param target_shape: maya shape node
    :type target_shape: str
    """

    # loop on user defined attributes if any
    for attr in cmds.listAttr(source_shape, userDefined=True) or []:

        # get attribute type and value
        attr_type = cmds.getAttr(source_shape + "." + attr, type=True)
        attr_value = cmds.getAttr(source_shape + "." + attr)

        # checks if attribute exists on target shape
        if not cmds.objExists(target_shape + '.' + attr):
            # handles attribute type attributes
            try:
                cmds.addAttr(target_shape, longName=attr,
                             attributeType=attr_type)

            # handles data type attributes
            except RuntimeError:
                cmds.addAttr(target_shape, longName=attr,
                             dataType=attr_type)

        # updates the attribute values
        try:
            # handles most general attribute cases
            cmds.setAttr(source_shape + "." + attr, attr_value)

        except RuntimeError:
            # handles array type attributes
            # .. todo:: Support all types of Maya attributes
            if 'Array' in attr_type:
                cmds.setAttr(target_shape + "." + attr, len(attr_value),
                             *((x, y, z) for x, y, z in attr_value),
                             type=attr_type)

            # handles extra attribute types
            else:
                cmds.setAttr(target_shape + "." + attr, attr_value,
                             type=attr_type)
