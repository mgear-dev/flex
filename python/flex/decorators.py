
""" flex.decorators

flex.decorators module contains utility functions that you can use as functions
decorators.

:module: flex.decorators
"""

# imports
import time
from maya import cmds


def kill_flex_ui(function):
    """ Kill an already existing Flex ui

    Checks if a existing instance of the Flex UI is open and kills it.

    :param function: your decorated function
    :type function: function

    :return: your decorated function
    :rtype: function
    """

    # checks for Flex ui instance
    if cmds.window("flex_qdialog", exists=True):
        cmds.deleteUI("flex_qdialog")

    def wrapper_function(*args, **kwars):
        # runs decorated function
        function_exec = function(*args, **kwars)

        return function_exec

    return wrapper_function


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
