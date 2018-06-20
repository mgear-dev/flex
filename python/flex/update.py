
""" flex.update

flex.update module handles the updating rig process

:module: flex.update
"""

# imports
from flex.query import get_prefix_from_elem, get_shapes_from_elem


def update_shape(source_shape, target_shape):
    print 'source: {} / target: {}'.format(source_shape, target_shape)
    return source_shape, target_shape


def update_rig(source, target, constant_prefix):
    """ Updates all shapes from the given source group to the target group

    :param source: maya transform node
    :type group: string

    :param target: maya transform node
    :type group: string

    :param constant_prefix: all shapes on source have a constant prefix
    :type constant_prefix: bool
    """

    # gets the shapes from source and target
    source_shapes = get_shapes_from_elem(source)
    target_shapes = get_shapes_from_elem(target)

    # gets prefix from source
    source_prefix = get_prefix_from_elem(source)
    target_prefix = get_prefix_from_elem(target)

    print source_prefix
    print target_prefix

    '''
    for shape in source_shapes:
        target_name = shape

        if not constant_prefix:
            prefix = get_prefix_from_elem(shape)

        target_name = shape.replace(prefix, '')

        if target_name not in target_shapes:
            continue

        update_shape(shape, target_name)
    '''
