
# imports
from maya import cmds
from flex.query import get_shapes_from_elem


def test_get_shapes_from_elem(initialize_maya):  # @UnusedVariable
    """ Test for the get_shapes_from_elem method """

    # create a sphere with a skin cluster
    mesh = cmds.polySphere(name='my_test_sphere_MESH', ch=True)
    skin_joint = cmds.createNode('joint', name='my_test_joint')
    cmds.skinCluster(skin_joint, mesh[0])

    assert get_shapes_from_elem(mesh[0]) == ['my_test_sphere_MESHShape']
