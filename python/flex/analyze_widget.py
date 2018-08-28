
""" flex.analyze_widget

Contains the Flex Analyze interface

:module: flex.analyze_widget
"""


# imports
from PySide2 import QtWidgets, QtGui, QtCore
from mgear.flex.query import get_resources_path
from mgear.flex.colors import YELLOW


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
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

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
        h_header.setPalette(YELLOW)
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
