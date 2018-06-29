
""" flex.ui

Contains the Flex user interface

:module: flex.ui
"""

# imports
from PySide2 import QtWidgets


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

        self.setObjectName('flex_qdialog')
        self.setWindowTitle("mGear: Flex (rig updater)")
        self.setFixedSize(300, 100)

        # ---------------------------------------------------------------------
        #                       creates widgets
        # ---------------------------------------------------------------------

        # layout widgets
        self.grid_layout = QtWidgets.QGridLayout()
        self.grid_layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.grid_layout)

        # source widgets
        self.source_text = QtWidgets.QLineEdit()
        self.source_text.setPlaceholderText("source group")
        self.add_source_button = QtWidgets.QPushButton("<--  source")
        self.add_source_button.setObjectName("source_qpushbutton")

        # target widgets
        self.target_text = QtWidgets.QLineEdit()
        self.target_text.setPlaceholderText("target group")
        self.add_target_button = QtWidgets.QPushButton("<--  target")
        self.add_target_button.setObjectName("target_qpushbutton")

        # run widget
        self.run_button = QtWidgets.QPushButton('--> Update shapes <--')

        # adds widgets to layout
        self.grid_layout.addWidget(self.source_text, 0, 0, 1, 2)
        self.grid_layout.addWidget(self.add_source_button, 0, 2, 1, 1)
        self.grid_layout.addWidget(self.target_text, 1, 0, 1, 2)
        self.grid_layout.addWidget(self.add_target_button, 1, 2, 1, 1)
        self.grid_layout.addWidget(self.run_button, 2, 0, 1, 3)
