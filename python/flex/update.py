
""" flex.update

flex.update module handles the updating rig process

:module: flex.update
"""

# imports
import logging
from flex.query import get_matching_shapes, get_shapes_from_group, get_prefix_less_dict, \
    get_missing_shapes

logger = logging.getLogger('mGear: Flex')
logger.setLevel(logging.DEBUG)


# @timer
def update_rig(source, target):
    """ Updates all shapes from the given source group to the target group

    :param source: maya transform node
    :type group: string

    :param target: maya transform node
    :type group: string
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

    logger.info(matching_shapes)
    logger.info(missing_source_shapes)
    logger.info(missing_target_shapes)


def update_shape(source_shape, target_shape):
    return source_shape, target_shape
