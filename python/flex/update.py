
""" flex.update

flex.update module handles the updating rig process

:module: flex.update
"""

# imports
from flex.query import get_updatable_shapes


def update_rig(source, target):
    """ Updates all shapes from the given source group to the target group

    :param source: maya transform node
    :type group: string

    :param target: maya transform node
    :type group: string

    :return: failed and succeeded updated shapes
    :rtype: dict
    """

    return get_updatable_shapes(source, target)
