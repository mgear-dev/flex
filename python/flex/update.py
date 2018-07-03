
""" flex.update

flex.update module handles the updating rig process

:module: flex.update
"""

# imports
import logging
from maya import OpenMaya
from maya import cmds
from maya import mel
from .decorators import timer
from .query import (get_matching_shapes, get_shapes_from_group,
                    get_prefix_less_dict, get_missing_shapes,
                    get_shape_orig)

logger = logging.getLogger("mGear: Flex")
logger.setLevel(logging.DEBUG)


def add_attribute(source, target, attribute_name):
    """ Adds the given attribute to the given object

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

    # adds the elements into an maya selection list
    m_selectin_list = OpenMaya.MSelectionList()
    m_selectin_list.add(source)

    # gets the element MObject
    m_object = OpenMaya.MObject()
    m_selectin_list.getDependNode(0, m_object)

    # gets the given attribute_name plug
    m_depend_node = OpenMaya.MFnDependencyNode(m_object)
    m_attribute = m_depend_node.findPlug(attribute_name).attribute()

    # gets the addAttr command from the MFnAttribute function
    fn_attr = OpenMaya.MFnAttribute(m_attribute)
    add_attr_cmd = fn_attr.getAddAttrCmd()[1:-1]

    # creates the attribute on the target
    mel.eval("{} {}".format(add_attr_cmd, target))


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
def update_rig(source, target, dry_run=True, deformed=True,
               user_attributes=True):
    """ Updates all shapes from the given source group to the target group

    :param source: maya transform node
    :type group: str

    :param target: maya transform node
    :type group: str

    :param deformed: deformed shapes update option
    :type deformed: bool

    :param user_attributes: user defined attributes update option
    :type user_attributes: bool
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

    if not dry_run:
        for shape in matching_shapes:
            logger.info("Updating: {}".format(shape))

            if deformed:
                update_deformed_shape(shape, matching_shapes[shape])

            if user_attributes:
                update_user_attributes(shape, matching_shapes[shape])

    logger.info("Source missing shapes: {}" .format(missing_source_shapes))
    logger.info("Target missing shapes: {}" .format(missing_target_shapes))


def update_deformed_shape(source_shape, target_shape):
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

    .. important:: Compound attributes types are not been handle yet.
    """

    # loop on user defined attributes if any
    for attr in cmds.listAttr(source_shape, userDefined=True) or []:

        # get attribute type and value
        attr_type = cmds.getAttr(source_shape + "." + attr, type=True)
        attr_value = cmds.getAttr(source_shape + "." + attr)

        # adds attribute on shape
        add_attribute(source_shape, target_shape, attr)

        # if there is no attr_value leave the attribute as it is
        if not attr_value:
            continue

        # updates the attribute values
        update_attribute(target_shape, attr, attr_type, attr_value)
