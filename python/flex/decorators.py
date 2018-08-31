
""" flex.decorators

flex.decorators module contains utility functions that you can use as functions
decorators.

:module: flex.decorators
"""

# imports
from maya import cmds
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
