
""" flex.ui

Contains the Flex user interface

:module: flex.ui
"""

# imports
from PySide2 import QtWidgets, QtGui, QtCore
from mgear.flex.query import get_resources_path

# colours
red = QtGui.QColor(250, 110, 90)
green = QtGui.QColor(35, 160, 140)
yellow = QtGui.QColor(250, 200, 120)
blue = QtGui.QColor(35, 140, 160)
yellow = QtGui.QColor(250, 200, 120)


class FlexAnalyzeDialog(QtWidgets.QDialog):
    """ The Flex analyze widgets

    Flex analyze is a side by side list widget style that will allow you to
    check which shapes matches.
    """

    def __init__(self, parent=None):
        """ Creates all the user interface widgets

        :param parent: the parent widget for the Flex dialog widget
        :type parent: PySide2.QtWidgets
        """
        super(FlexAnalyzeDialog, self).__init__(parent=parent)

        # sets window rules
        self.setObjectName("flex_analyse_qdialog")
        self.setWindowTitle("mGear: Flex analyze shapes")
        self.setMinimumWidth(500)

        # creates layout
        layout = QtWidgets.QVBoxLayout()
        layout.setMargin(0)

        # setup table
        self.setLayout(layout)
        self.__create_table()

        # add widgets
        layout.addWidget(self.table_widget)

    def __create_table(self):
        """ Creates the table widget

        We could use a table view on this case as well but for now I am keeping
        if as a widget as the table is used only to represent a non changing
        state of data.
        """

        # creates the table
        self.table_widget = QtWidgets.QTableWidget()
        self.table_widget.setColumnCount(5)
        self.table_widget.setIconSize(QtCore.QSize(20, 20))

        # adds headers
        self.table_widget.setHorizontalHeaderLabels(["Source",
                                                     "Target",
                                                     "Type",
                                                     "Count",
                                                     "B-Box"])

        # setup headers look and feel
        h_header = self.table_widget.horizontalHeader()
        h_header.setPalette(yellow)
        h_header.setFixedHeight(21)
        h_header.setDefaultSectionSize(40)
        h_header.setSectionResizeMode(h_header.Stretch)
        h_header.setSectionResizeMode(2, h_header.Fixed)
        h_header.setSectionResizeMode(3, h_header.Fixed)
        h_header.setSectionResizeMode(4, h_header.Fixed)
        h_header.setSectionsClickable(False)

        # hides vertical header
        self.table_widget.verticalHeader().setVisible(False)

    def add_items(self, source, target):
        """ Handles adding items to the table widget

        :param source: the source shape element
        :type source: string

        :param target: the target corresponding shape element matching source
        :type target: string
        """

        # creates the icons
        green_icon = QtGui.QIcon()
        image = QtGui.QPixmap("{}/green.png".format(get_resources_path()))
        green_icon.addPixmap(image)

        red_icon = QtGui.QIcon()
        image = QtGui.QPixmap("{}/red.png".format(get_resources_path()))
        red_icon.addPixmap(image)

        # source item
        source_item = QtWidgets.QTableWidgetItem()
        source_item.setTextAlignment(QtCore.Qt.AlignCenter)
        source_item.setText(source)
        source_item.setFlags(QtCore.Qt.ItemIsSelectable |
                             QtCore.Qt.ItemIsEnabled)

        # target item
        target_item = QtWidgets.QTableWidgetItem()
        target_item.setTextAlignment(QtCore.Qt.AlignCenter)
        target_item.setText(target)
        target_item.setFlags(QtCore.Qt.ItemIsSelectable |
                             QtCore.Qt.ItemIsEnabled)

        # type item
        type_item = QtWidgets.QTableWidgetItem()
        type_item.setIcon(green_icon)
        type_item.setFlags(QtCore.Qt.ItemIsEnabled)

        # type item
        count_item = QtWidgets.QTableWidgetItem()
        count_item.setIcon(red_icon)
        count_item.setFlags(QtCore.Qt.ItemIsEnabled)

        # insert items
        self.table_widget.insertRow(0)
        self.table_widget.setRowHeight(0, 19)
        self.table_widget.setItem(0, 0, source_item)
        self.table_widget.setItem(0, 1, target_item)
        self.table_widget.setItem(0, 2, type_item)
        self.table_widget.setItem(0, 3, count_item)


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
        self.setObjectName("flex_qdialog")
        self.setWindowTitle("mGear: Flex (rig updater)")
        self.setStyleSheet(self.__style_sheet())
        self.setMinimumWidth(350)
        self.setMinimumHeight(100)

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
                 "padding:0px 10px;}"
                 "QHeaderView{"
                 "border:0px;"
                 "padding: 0px;"
                 "margin: 0px;}"
                 "QTableView{"
                 "margin:10px;"
                 "padding:0px;}")

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

        # create layout
        grid_layout = QtWidgets.QGridLayout()

        # creates group box
        group_box = QtWidgets.QGroupBox()
        group_box.setTitle("MODEL GROUPS")
        group_box.setLayout(grid_layout)
        group_box.setFixedHeight(80)
        group_box.setMinimumHeight(0)

        # source widgets
        self.source_text = QtWidgets.QLineEdit()
        self.source_text.setObjectName("source_qlineedit")
        self.source_text.setPlaceholderText("source group")
        self.source_text.setStatusTip(
            "Type the name of your source group here")
        self.add_source_button = QtWidgets.QPushButton("<--  source")
        self.add_source_button.setObjectName("source_qpushbutton")
        self.add_source_button.setPalette(yellow)
        self.add_source_button.setStatusTip("Add selected source group")

        # target widgets
        self.target_text = QtWidgets.QLineEdit()
        self.target_text.setObjectName("target_qlineedit")
        self.target_text.setPlaceholderText("target group")
        self.target_text.setStatusTip(
            "Type the name of your target group here")
        self.add_target_button = QtWidgets.QPushButton("<--  target")
        self.add_target_button.setObjectName("target_qpushbutton")
        self.add_target_button.setPalette(blue)
        self.add_target_button.setStatusTip("Add selected target group")

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

        # create layout
        vertical_layout = QtWidgets.QVBoxLayout()

        # creates group box
        group_box = QtWidgets.QGroupBox()
        group_box.setTitle("RUN")
        group_box.setLayout(vertical_layout)
        group_box.setFixedHeight(80)

        # analyse widget
        self.analyse_button = QtWidgets.QPushButton("Analyze")
        self.analyse_button.setPalette(green)
        self.analyse_button.setStatusTip(
            "Hit to analyze the source and target shapes")

        # run widget
        self.run_button = QtWidgets.QPushButton("--> Update shapes <--")
        self.run_button.setPalette(red)
        self.run_button.setStatusTip("Hit to execute updating your rig shapes")

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
        group_box.setMinimumHeight(0)

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

        # Transformed & Deformed
        t_n_d_widget = QtWidgets.QWidget()
        t_n_d_layout = QtWidgets.QHBoxLayout()
        t_n_d_layout.setContentsMargins(0, 0, 0, 0)
        t_n_d_widget.setContentsMargins(0, 0, 0, 0)
        t_n_d_widget.setLayout(t_n_d_layout)

        # deformed
        self.deformed_check = QtWidgets.QGroupBox("Deformed")
        self.deformed_check.setCheckable(True)
        self.deformed_check.setChecked(True)

        # transformed
        self.transformed_check = QtWidgets.QGroupBox("Transformed")
        self.transformed_check.setCheckable(True)
        self.transformed_check.setChecked(True)
        transformed_layout = QtWidgets.QVBoxLayout()
        transformed_layout.setAlignment(QtCore.Qt.AlignHCenter)
        self.transformed_check.setLayout(transformed_layout)

        # hold position values
        self.transformed_hold_check = QtWidgets.QRadioButton(
            "Hold position values")
        self.transformed_hold_check.setChecked(True)
        # new position values
        self.transformed_new_check = QtWidgets.QRadioButton(
            "New position values")

        # add widgets to transformed group box
        transformed_layout.addWidget(self.transformed_hold_check)
        transformed_layout.addWidget(self.transformed_new_check)

        # add to layout
        t_n_d_layout.addWidget(self.transformed_check)
        t_n_d_layout.addWidget(self.deformed_check)

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
        grid_layout.addWidget(self.vertex_colours_check, 1, 2, 1, 1)
        grid_layout.addWidget(self.display_attributes_check, 1, 0, 1, 1)
        grid_layout.addWidget(self.component_attributes_check, 1, 1, 1, 1)
        grid_layout.addWidget(t_n_d_widget, 2, 0, 1, 3)

        # adds the group box widget to the widgets_layout
        self.widgets_layout.addWidget(group_box)
