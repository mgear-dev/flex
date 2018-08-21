
""" flex.decorators

flex.decorators module contains utility functions that you can use as functions
decorators.

:module: flex.decorators
"""

# imports
from maya import cmds
import maya.OpenMayaUI as mui
import shiboken2 as shi
from PySide2 import QtCore as qc
from PySide2 import QtGui as qg
from PySide2 import QtWidgets as qw
import time


def finished_running(function):
    """ Displays a end of process viewport message

    :param function: your decorated function
    :type function: function

    :return: your decorated function
    :rtype: function
    """

    def wrapper_function(*args, **kwars):
        # runs decorated function
        function_exec = function(*args, **kwars)

        cmds.inViewMessage(message="Flex Finished running...", fade=True,
                           position="midCenter", fontSize=30, fadeStayTime=500,
                           fadeOutTime=100, dragKill=True, bkc=0x00154060,
                           alpha=0.7)

        return function_exec

    return wrapper_function


def clean_instances(object_name):

    def kill_flex_ui(function):
        """ Kill an already existing Flex ui

        Checks if a existing instance of the Flex UI is open and kills it.

        :param function: your decorated function
        :type function: function

        :return: your decorated function
        :rtype: function
        """

        # checks for Flex ui instance
        mayaMainWindowPtr = mui.MQtUtil.mainWindow()
        mayaMainWindow = shi.wrapInstance(
            long(mayaMainWindowPtr), qw.QMainWindow)

        # Go through main window's children to find any previous instances
        for obj in mayaMainWindow.children():
            if isinstance(obj, qw.QDialog) and obj.objectName() == object_name:
                obj.setParent(None)
                obj.deleteLater()
                print('Object {} deleted from memory'.format(obj))
                del(obj)

        def wrapper_function(*args, **kwars):
            # runs decorated function
            function_exec = function(*args, **kwars)

            return function_exec

        return wrapper_function

    return kill_flex_ui


def set_focus(function):
    """ Set focus on Flex window

    Sets focus on Flex UI.

    :param function: your decorated function
    :type function: function

    :return: your decorated function
    :rtype: function
    """

    def wrapper_function(*args, **kwars):
        # runs decorated function
        function_exec = function(*args, **kwars)
        cmds.setFocus("flex_qdialog")
        return function_exec

    return wrapper_function


def timer(function):
    """ Function timer

    Simple timer function decorator that you can use on Flex to time your code
    execution

    :param function: your decorated function
    :type function: function

    :return: your decorated function
    :rtype: function
    """

    def wrapper_function(*args, **kwars):
        # gets current time
        t1 = time.time()

        # runs decorated function
        function_exec = function(*args, **kwars)

        # gets new time
        t2 = time.time() - t1

        print 'function: {} took {}'.format(function.__name__, t2)

        return function_exec

    return wrapper_function
