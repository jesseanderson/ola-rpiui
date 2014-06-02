"""
Author: Sean Sill
File: __init__.py
Description: Loads all test files in the directory
Based on:
http://stackoverflow.com/questions/1896918/running-unittest-with-typical-test-directory-structure
"""

import os
import unittest
import logging

def create_test_suite(root='.'):
    module_strings  = find_tests_recursively('test', root)
    logging.info('Found %s modules.', len(module_strings))
    logging.debug("Module strings: %s", module_strings)
    logging.info('Attempting to import...')
    suites = [unittest.defaultTestLoader.loadTestsFromName(name) \
          for name in module_strings]
    logging.debug("Test suites found: %s", suites)
    testSuite = unittest.TestSuite(suites)
    return testSuite

def find_tests_recursively(parent_module, path=None):
    """
    Returns a list of module strings to import
    """
    if path == None:
        return [];
    module_strings = []
    files = os.listdir(path)
    for f in files:
        full_path = os.path.join(path, f)
        if os.path.isfile(full_path):
            if f[:5] == 'test_' and f[-3:] == '.py':
                module_strings.append(parent_module+'.'+f[:len(f)-3])
        elif os.path.isdir(full_path):
            module_strings.extend(
                    find_tests_recursively(parent_module+'.'+f, full_path))
    logging.debug(module_strings)
    return module_strings
