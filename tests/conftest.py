

# imports
import pytest
from maya import cmds


@pytest.fixture(scope='session')
def initialize_maya():
    """ Initialize Maya before calling the test """

    # uses pymel which will correctly initialize maya startup
    import pymel.core as pm  # @UnusedImport

    yield

    # quits Maya
    cmds.quit(force=True)
