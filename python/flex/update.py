
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


def add_shape_attribute(element, attribute_name, attribute_type):
    """ Adds the given attribute to the given object

    :param element: the maya node
    :type element: str

    :param attribute_name: the attribute name to add in the given element
    :type attribute_name: str

    :param attribute_type: the attribute type
    :type attribute_type: str
    """

    # check if attribute already exists
    if cmds.objExists("{}.{}".format(element, attribute_name)):
        return

    # handles attribute type attributes
    try:
        cmds.addAttr(element, longName=attribute_name,
                     attributeType=attribute_type)

    # handles data type attributes
    except RuntimeError:
        cmds.addAttr(element, longName=attribute_name, dataType=attribute_type)


def update_attribute(element, attribute_name, attribute_type, attribute_value):
    """ Updates the given attribute to the given value

    :param element: the maya node
    :type element: str

    :param attribute_name: the attribute name to add in the given element
    :type attribute_name: str

    :param attribute_type: the attribute type
    :type attribute_type: str

    :param attribute_value: value to set on the attribute
    :type attribute: maya attributes types

    .. todo:: Support all types of Maya attributes
    """

    try:
        cmds.setAttr("{}.{}".format(element, attribute_name), attribute_value)
        return
    except RuntimeError:
        pass

    try:
        cmds.setAttr("{}.{}".format(element, attribute_name), attribute_value,
                     type=attribute_type)
        return
    except RuntimeError:
        pass

    try:
        cmds.setAttr("{}.{}".format(element, attribute_name),
                     len(attribute_value),
                     *((x, y, z) for x, y, z in attribute_value),
                     type=attribute_type)
        return
    except RuntimeError:
        pass


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

    if not source_shapes or not target_shapes:
        message = "No shape(s) found under the given groups"
        logger.error(message)
        raise ValueError(message)

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
        update_user_attributes(shape, matching_shapes[shape])

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


def update_user_attributes(source_shape, target_shape):
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

        # adds attribute on shape
        add_shape_attribute(target_shape, attr, attr_type)

        # updates the attribute values
        update_attribute(target_shape, attr, attr_type, attr_value)
