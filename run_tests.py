"""
Author: Sean Sill
Description: Runs all unittests in directory
"""

import os, sys
import time
import test
import unittest
import logging

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    path_to_tests =  os.path.dirname(__file__)
    path_to_lib = os.path.abspath(os.path.join(path_to_tests, os.pardir))
    sys.path.insert(0, path_to_lib)
    suites = test.create_test_suite('test')
    testSuite = unittest.TestSuite(suites)
    print 'Running all tests in test'
    test_runner = unittest.TextTestRunner().run(testSuite)
