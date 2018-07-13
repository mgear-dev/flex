
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
        self.setStyleSheet(self.__style_sheet())
        self.setMinimumWidth(350)

        # creates widgets
        self.layout_widgets()
        self.models_groups_widgets()
        self.options_widgets()
        self.run_widgets()

    def __style_sheet(self):
        """ Hard coded style sheet

        :return: the hard coded style sheet
        :rtype: str
        """

        style = ("QFrame{"
                 "border:1px solid gray;"
                 "border-radius:2px;"
                 "margin: 0px;"
                 "padding: 8px;}"
                 "QGroupBox{"
                 "border:1px solid gray;"
                 "border-radius:2px;"
                 "margin-top: 2ex;}"
                 "QGroupBox::title{"
                 "subcontrol-origin: margin;"
                 "subcontrol-position: top center;"
                 "padding:0px 10px;}")

        return style

    def layout_widgets(self):
        """ Creates the general UI layouts
        """

        # layout widgets
        main_vertical_layout = QtWidgets.QVBoxLayout()
        main_vertical_layout.setMargin(0)
        self.setLayout(main_vertical_layout)

        # frame
        model_frame = QtWidgets.QFrame()
        self.widgets_layout = QtWidgets.QVBoxLayout()
        self.widgets_layout.setMargin(0)
        self.widgets_layout.setSpacing(10)
        model_frame.setLayout(self.widgets_layout)

        # adds widgets layout
        main_vertical_layout.addWidget(model_frame)

    def models_groups_widgets(self):
        """ Creates the source and target widgets area
        """

        # colours
        blue = QtGui.QColor(35, 140, 160)
        yellow = QtGui.QColor(250, 200, 120)

        # create layout
        grid_layout = QtWidgets.QGridLayout()

        # creates group box
        group_box = QtWidgets.QGroupBox()
        group_box.setTitle("MODEL GROUPS")
        group_box.setLayout(grid_layout)

        # source widgets
        self.source_text = QtWidgets.QLineEdit()
        self.source_text.setObjectName("source_qlineedit")
        self.source_text.setPlaceholderText("source group")
        self.add_source_button = QtWidgets.QPushButton("<--  source")
        self.add_source_button.setObjectName("source_qpushbutton")
        self.add_source_button.setPalette(yellow)

        # target widgets
        self.target_text = QtWidgets.QLineEdit()
        self.target_text.setObjectName("target_qlineedit")
        self.target_text.setPlaceholderText("target group")
        self.add_target_button = QtWidgets.QPushButton("<--  target")
        self.add_target_button.setObjectName("target_qpushbutton")
        self.add_target_button.setPalette(blue)

        # adds widgets to layout
        grid_layout.addWidget(self.source_text, 0, 0, 1, 2)
        grid_layout.addWidget(self.add_source_button, 0, 2, 1, 1)
        grid_layout.addWidget(self.target_text, 1, 0, 1, 2)
        grid_layout.addWidget(self.add_target_button, 1, 2, 1, 1)

        # adds the group box widget to the widgets_layout
        self.widgets_layout.addWidget(group_box)

    def run_widgets(self):
        """ Creates the run widgets area
        """

        # colours
        red = QtGui.QColor(250, 110, 90)
        green = QtGui.QColor(35, 160, 140)

        # create layout
        vertical_layout = QtWidgets.QVBoxLayout()

        # creates group box
        group_box = QtWidgets.QGroupBox()
        group_box.setTitle("RUN")
        group_box.setLayout(vertical_layout)

        # analyse widget
        self.analyse_button = QtWidgets.QPushButton("Analyze")
        self.analyse_button.setPalette(green)

        # run widget
        self.run_button = QtWidgets.QPushButton("--> Update shapes <--")
        self.run_button.setPalette(red)

        # adds widget to layout
        vertical_layout.addWidget(self.analyse_button)
        vertical_layout.addWidget(self.run_button)

        # adds the group box widget to the widgets_layout
        self.widgets_layout.addWidget(group_box)

    def options_widgets(self):
        """ Create the options widget area
        """
        # create layout
        grid_layout = QtWidgets.QGridLayout()

        # creates group box
        group_box = QtWidgets.QGroupBox()
        group_box.setTitle("OPTIONS")
        group_box.setLayout(grid_layout)

        # user defined attributes
        self.user_attributes_check = QtWidgets.QCheckBox("User Attributes")
        self.user_attributes_check.setChecked(True)

        # plug-in attributes
        self.plugin_attributes_check = QtWidgets.QCheckBox("Plug-in "
                                                           "Attributes")
        self.plugin_attributes_check.setChecked(False)

        # render attributes
        self.render_attributes_check = QtWidgets.QCheckBox("Render Attributes")
        self.render_attributes_check.setChecked(True)

        # vertex colours
        self.vertex_colours_check = QtWidgets.QCheckBox("Vertex Colours")
        self.vertex_colours_check.setChecked(True)
        self.vertex_colours_check.setEnabled(False)

        # deformed
        self.deformed_check = QtWidgets.QCheckBox("Deformed")
        self.deformed_check.setChecked(True)

        # transformed
        self.transformed_check = QtWidgets.QCheckBox("Transformed")
        self.transformed_check.setChecked(False)
        self.transformed_check.setEnabled(False)

        # object display
        self.display_attributes_check = QtWidgets.QCheckBox(
            "Object Display Attrs.")
        self.display_attributes_check.setChecked(False)

        # component display
        self.component_attributes_check = QtWidgets.QCheckBox(
            "Component Display Attrs.")
        self.component_attributes_check.setChecked(False)

        # adds widgets to layout
        grid_layout.addWidget(self.user_attributes_check, 0, 0, 1, 1)
        grid_layout.addWidget(self.plugin_attributes_check, 0, 1, 1, 1)
        grid_layout.addWidget(self.render_attributes_check, 0, 2, 1, 1)
        grid_layout.addWidget(self.deformed_check, 1, 0, 1, 1)
        grid_layout.addWidget(self.transformed_check, 1, 1, 1, 1)
        grid_layout.addWidget(self.vertex_colours_check, 1, 2, 1, 1)
        grid_layout.addWidget(self.display_attributes_check, 2, 0, 1, 1)
        grid_layout.addWidget(self.component_attributes_check, 2, 1, 1, 1)

        # adds the group box widget to the widgets_layout
        self.widgets_layout.addWidget(group_box)
