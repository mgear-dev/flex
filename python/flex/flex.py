
""" flex.flex

Flex is the main module that allows you to run the update tool

:module: flex.flex
"""

# imports
from __future__ import absolute_import

from PySide2 import QtWidgets
from maya import OpenMayaUI
from shiboken2 import wrapInstance

from mgear.flex.decorators import finished_running
from mgear.flex.decorators import set_focus
from mgear.flex.query import get_transform_selection
from mgear.flex.query import is_maya_batch
from mgear.flex.query import is_valid_group
from mgear.flex.ui import FlexDialog
from mgear.flex.update import update_rig


# flex imports
class Flex(object):
    """ Flex is the mGear rig update tool

    Flex class object allows you to trigger updates on a given rig.
    You can use this object to execute the update with specific features
    """

    def __init__(self):
        super(Flex, self).__init__()

        # define properties
        self.__source_group = None
        self.__target_group = None
        self.__user_attributes = True

        # initialise Flex user interface
        self.ui = FlexDialog(self.__warp_maya_window())

        # connect user interface signals
        self.__setup_ui_signals()

    def __property_check(self, value):
        """ Flex properties check

        :param value: value to check
        :type value: type
        """

        if value and not is_valid_group(value):
            raise ValueError("The given group ({}) is not a valid Maya "
                             "transform node or it simply doesn't exist on "
                             " your current Maya session".format(value))

        if self.source_group == self.target_group and not value:
            raise ValueError("The given source and target objects are the same"
                             ". Nothing to update!")

    def __gather_ui_options(self):
        """ Gathers all the UI execution options available in a dict

        :return: A dict with the bool statements of options gathered
        :rtype: dict

        .. important: This is a list of options that need to be gathered.
           * deformed
           * transformed
           * object_display
           * component_display
           * render_attributes
           * plugin_attributes
        """
        # gather ui options
        ui_options = {}

        ui_options["deformed"] = self.ui.deformed_check.isChecked()
        ui_options["transformed"] = self.ui.transformed_check.isChecked()
        ui_options["user_attributes"] = (
            self.ui.user_attributes_check.isChecked())
        ui_options["object_display"] = (
            self.ui.display_attributes_check.isChecked())
        ui_options["component_display"] = (
            self.ui.component_attributes_check.isChecked())
        ui_options["render_attributes"] = (
            self.ui.render_attributes_check.isChecked())
        ui_options["plugin_attributes"] = (
            self.ui.plugin_attributes_check.isChecked())

        return ui_options

    def __repr__(self):
        return "{}".format(self.__class__)

    def __set_button_edits(self, widget):
        """ "Sets Flex source and target groups properties

        When triggering the push buttons Flex properties gets updated.

        :param widget: the widget been edited
        :type widget: PySide2.QtWidgets
        """

        widget_name = widget.objectName().split("_")[0]
        value = get_transform_selection()

        if widget_name == "source":
            self.source_group = value
            self.ui.source_text.setText(value)
        else:
            self.target_group = value
            self.ui.target_text.setText(value)

    def __set_text_edits(self, widget):
        """ Updates Flex source and target groups properties

        When typing inside the text widget the properties gets updated.

        :param widget: the widget been edited
        :type widget: PySide2.QtWidgets
        """

        widget_name = widget.objectName().split("_")[0]

        if widget_name == "source":
            if not self.ui.source_text.text():
                self.source_group = None
                return
            self.source_group = self.ui.source_text.text()
            return

        else:
            if not self.ui.target_text.text():
                self.target_group = None
                return
            self.target_group = self.ui.target_text.text()
            return

    def __setup_ui_signals(self):
        """ Setups how the UI interacts with the API and the tool

        Connects the widget signals to Flex methods
        """

        # source button
        self.ui.add_source_button.clicked.connect(
            lambda: self.__set_button_edits(self.ui.add_source_button))
        # target button
        self.ui.add_target_button.clicked.connect(
            lambda: self.__set_button_edits(self.ui.add_target_button))

        # source text edit
        self.ui.source_text.textEdited.connect(
            lambda: self.__set_text_edits(self.ui.source_text))
        # target text edit
        self.ui.target_text.textEdited.connect(
            lambda: self.__set_text_edits(self.ui.target_text))

        # analyse button
        self.ui.analyse_button.clicked.connect(self.update_rig)

        # run button
        self.ui.run_button.clicked.connect(
            lambda: self.update_rig(analytic=False))

    def __str__(self):
        return "mGear: Flex == > An awesome rig update tool"

    def __update_ui(self):
        """ Updates the ui content
        """

        if self.ui.isVisible():
            self.ui.source_text.setText(self.__source_group)
            self.ui.target_text.setText(self.__target_group)

    @staticmethod
    def __warp_maya_window():
        """ Returns a qt widget warp of the Maya window

        :return: Maya window on a qt widget. Returns None if Maya is on batch
        :rtype: PySide2.QtWidgets or None
        """

        if not is_maya_batch:
            return None

        # gets Maya main window object
        maya_window = OpenMayaUI.MQtUtil.mainWindow()
        return wrapInstance(long(maya_window), QtWidgets.QDialog)

    @set_focus
    def launch(self):
        """ Displays the user interface
        """

        if not is_maya_batch():
            self.ui.show()
            self.__update_ui()

    @property
    def source_group(self):
        """ Flex source group name (property)
        """

        return self.__source_group

    @source_group.setter
    def source_group(self, value):
        """ Setter for the source_group property

        :param value: Maya transform node name containing all the source shapes
        :type value: str
        """

        # set value
        self.__source_group = value

        # ui update
        self.__update_ui()

    @property
    def target_group(self):
        """ Flex target group name (property)
        """

        return self.__target_group

    @target_group.setter
    def target_group(self, value):
        """ Setter for the target_group property

        :param value: Maya transform node name containing all the target shapes
        :type value: str
        """

        # set value
        self.__target_group = value

        # ui update
        self.__update_ui()

    @finished_running
    def update_rig(self, analytic=True, run_options=None):
        """ Launches the rig update process

        :param analytic: Update rig runs in analytic mode
        :type analytic: bool

        :param run_options: Options that will be used during the rig update
        :type run_options: dict
        """

        message = ("You need to provided a source and target group in order to"
                   " run the rig update.")

        # check if values have been set
        if not self.source_group or not self.target_group:
            raise ValueError(message)

        # check if values are correct
        self.__property_check(None)

        if not run_options:
            run_options = self.__gather_ui_options()

        # triggers the update
        update_rig(source=self.source_group, target=self.target_group,
                   options=run_options, analytic=analytic)
