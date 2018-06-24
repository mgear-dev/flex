
""" flex.decorators

flex.decorators module contains utility functions that you can use as functions
decorators.

:module: flex.decorators
"""

# imports
import time


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
