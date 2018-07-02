
""" flex.ui

Contains the Flex user interface

:module: flex.ui
"""

# imports
from PySide2 import QtWidgets, QtGui


class FlexDialog(QtWidgets.QDialog):
    """ The Flex UI widgets

    Flex UI contains several options you can tweak to customise your rig update
    """

    def __init__(self, parent=None):
        """ Creates all the user interface widgets

        :param parent: the parent widget for the Flex dialog widget
        :type parent: PySide2.QtWidgets
        """
        super(FlexDialog, self).__init__(parent=parent)

        # sets window rules
        self.setObjectName('flex_qdialog')
        self.setWindowTitle("mGear: Flex (rig updater)")
        self.setFixedSize(300, 100)

        # creates widgets
        self.create_layout_widgets()
        self.create_source_target_widgets()
        self.create_run_widgets()
        self.layout_widgets()

    def create_layout_widgets(self):
        """ Creates the general UI layouts
        """

        # layout widgets
        self.grid_layout = QtWidgets.QGridLayout()
        self.grid_layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.grid_layout)

    def create_run_widgets(self):
        """ Creates the run widgets area
        """

        # colors
        red = QtGui.QColor(250, 110, 90)

        # run widget
        self.run_button = QtWidgets.QPushButton('--> Update shapes <--')
        self.run_button.setPalette(red)

    def create_source_target_widgets(self):
        """ Creates the source and target widgets area
        """

        # colors
        blue = QtGui.QColor(35, 140, 160)
        yellow = QtGui.QColor(250, 200, 120)

        # source widgets
        self.source_text = QtWidgets.QLineEdit()
        self.source_text.setPlaceholderText("source group")
        self.add_source_button = QtWidgets.QPushButton("<--  source")
        self.add_source_button.setObjectName("source_qpushbutton")
        self.add_source_button.setPalette(yellow)

        # target widgets
        self.target_text = QtWidgets.QLineEdit()
        self.target_text.setPlaceholderText("target group")
        self.add_target_button = QtWidgets.QPushButton("<--  target")
        self.add_target_button.setObjectName("target_qpushbutton")
        self.add_target_button.setPalette(blue)

    def layout_widgets(self):
        """ Adds the widgets to the layout
        """

        # adds widgets to layout
        self.grid_layout.addWidget(self.source_text, 0, 0, 1, 2)
        self.grid_layout.addWidget(self.add_source_button, 0, 2, 1, 1)
        self.grid_layout.addWidget(self.target_text, 1, 0, 1, 2)
        self.grid_layout.addWidget(self.add_target_button, 1, 2, 1, 1)
        self.grid_layout.addWidget(self.run_button, 2, 0, 1, 3)
