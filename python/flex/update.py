
""" flex.update

flex.update module handles the updating rig process

:module: flex.update
"""

# imports
import logging
from maya import OpenMaya
from maya import cmds
from maya import mel

# flex imports
from .attributes import COMPONENT_DISPLAY_ATTRIBUTES
from .attributes import OBJECT_DISPLAY_ATTRIBUTES
from .attributes import RENDER_STATS_ATTRIBUTES
from .decorators import timer
from .query import get_dependency_node
from .query import get_matching_shapes
from .query import get_missing_shapes
from .query import get_prefix_less_dict
from .query import get_shape_orig
from .query import get_shapes_from_group
from .query import is_lock_attribute
from .query import lock_unlock_attribute

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

    # gets the given attribute_name plug
    m_depend_node = get_dependency_node(source)
    attribute = m_depend_node.findPlug(attribute_name)

    # gets the setAttr command from the MPlug function
    command = []
    attribute.getSetAttrCmds(command, attribute.kAll, True)

    # returns if command wans't fount
    if not command:
        logger.error("The given attribute can't be set: {}".format(
                     attribute_name))
        return

    # formats the command
    set_attr_cmds = command[0].replace(".{}".format(attribute_name),
                                       "{}.{}".format(target, attribute_name))

    # checks for locking
    lock = is_lock_attribute(target, attribute_name)

    if not lock_unlock_attribute(target, attribute_name, False):
        logger.error("The given attribute ({}) can't be updated on {}"
                     .format(attribute_name, target))
        return

    # sets the attribute value
    mel.eval(set_attr_cmds)

    if lock:
        lock_unlock_attribute(target, attribute_name, True)


def update_deformed_shape(source, target):
    """ Updates the target shape with the given source shape content

    :param source: maya shape node
    :type source: str

    :param target: maya shape node
    :type target: str
    """

    deform_origin = get_shape_orig(target)

    if not deform_origin:
        return

    deform_origin = deform_origin[0]

    # updates the shape
    cmds.connectAttr("{}.outMesh".format(source),
                     "{}.inMesh".format(deform_origin), force=True)

    # forces shape evaluation to achieve the update
    cmds.dgeval("{}.outMesh".format(target))

    # finish shape update
    cmds.disconnectAttr("{}.outMesh".format(source),
                        "{}.inMesh".format(deform_origin))


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
def update_rig(source, target, options, analytic=True):
    """ Updates all shapes from the given source group to the target group

    :param source: maya transform node
    :type source: str

    :param target: maya transform node
    :type target: str

    :param options: update options
    :type options: dict

    :param analytic: updating the rig in analytic mode
    :type analytic: bool
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

    if not analytic:
        for shape in matching_shapes:
            logger.info("Updating: {}".format(shape))

            if options["deformed"]:
                update_deformed_shape(shape, matching_shapes[shape])

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

    logger.info("Source missing shapes: {}" .format(missing_source_shapes))
    logger.info("Target missing shapes: {}" .format(missing_target_shapes))


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
