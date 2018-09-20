
# imports
from maya import cmds


def test_update_rig(initialize_maya, flex_object):  # @UnusedVariable
    """ Test the update_rig method of the Flex class
    """

    # opens test file
    cmds.file("D:/Work/Grid/projects/multi/flex/scenes/"
              "bigfoot_update_scene.ma", f=True, o=True)

    # sets the groups
    flex_object.source_group = "bigfoot_geo_topo_changed:geo"
    flex_object.target_group = "geo"

    assert flex_object.update_rig() is None
