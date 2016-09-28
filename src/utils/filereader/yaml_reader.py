# -*- coding: utf-8 -*-

import yaml
import json
import os
from src.utils.config import DefaultConfig
from src.utils.logger import Logger
from src.utils.filereader.parsing import *

# todo: yaml reader

DEFAULT_TIMEOUT = 10
logger = Logger(__name__).get_logger()


class TestConfig(object):
    """ Configuration for a test run """
    timeout = DEFAULT_TIMEOUT  # timeout of tests, in seconds
    print_bodies = False  # Print response bodies in all cases
    print_headers = False  # Print response bodies in all cases
    retries = 0  # Retries on failures
    test_parallel = False  # Allow parallel execution of tests in a test set, for speed?
    interactive = False
    verbose = False
    ssl_insecure = False
    skip_term_colors = False  # Turn off output term colors

    # Binding and creation of generators
    variable_binds = None
    generators = None  # Map of generator name to generator function

    def __str__(self):
        return json.dumps(self, default=safe_to_json)


class TestSet(object):
    """ Encapsulates a set of tests and test configuration for them """
    tests = list()
    benchmarks = list()
    config = TestConfig()

    def __init__(self):
        self.config = TestConfig()
        self.tests = list()
        self.benchmarks = list()

    def __str__(self):
        return json.dumps(self, default=safe_to_json)


def read_file(path):
    """ Read an input into a file, doing necessary conversions around relative path handling """
    with open(path, "r") as f:
        string = f.read()
        f.close()
    return string


def parse_testsets(base_url, test_structure, test_files=set(), working_directory=None, vars=None):
    """ Convert a Python data structure read from validated YAML to a set of structured testsets
    The data structure is assumed to be a list of dictionaries, each of which describes:
        - a tests (test structure)
        - a simple test (just a URL, and a minimal test is created)
        - or overall test configuration for this testset
        - an import (load another set of tests into this one, from a separate file)
            - For imports, these are recursive, and will use the parent config if none is present

    Note: test_files is used to track tests that import other tests, to avoid recursive loops

    This returns a list of testsets, corresponding to imported testsets and in-line multi-document sets
    """

    tests_out = list()
    test_config = TestConfig()
    testsets = list()
    benchmarks = list()

    if working_directory is None:
        working_directory = os.path.abspath(os.getcwd())

    if vars and isinstance(vars, dict):
        test_config.variable_binds = vars

    # returns a testconfig and collection of tests
    for node in test_structure:  # Iterate through lists of test and configuration elements
        if isinstance(node, dict):  # Each config element is a miniature key-value dictionary
            node = lowercase_keys(node)
            for key in node:
                if key == u'import':
                    importfile = node[key]  # import another file
                    if importfile not in test_files:
                        logger.debug("Importing test sets: " + importfile)
                        test_files.add(importfile)
                        import_test_structure = read_test_file(importfile)
                        with cd(os.path.dirname(os.path.realpath(importfile))):
                            import_testsets = parse_testsets(
                                base_url, import_test_structure, test_files, vars=vars)
                            testsets.extend(import_testsets)
                elif key == u'url':  # Simple test, just a GET to a URL
                    mytest = Test()
                    val = node[key]
                    assert isinstance(val, basestring)
                    mytest.url = base_url + val
                    tests_out.append(mytest)
                elif key == u'test':  # Complex test with additional parameters
                    with cd(working_directory):
                        child = node[key]
                        mytest = Test.parse_test(base_url, child)
                        tests_out.append(mytest)
                elif key == u'benchmark':
                    benchmark = parse_benchmark(base_url, node[key])
                    benchmarks.append(benchmark)
                elif key == u'config' or key == u'configuration':
                    test_config = parse_configuration(
                        node[key], base_config=test_config)
    testset = TestSet()
    testset.tests = tests_out
    testset.config = test_config
    testset.benchmarks = benchmarks
    testsets.append(testset)
    return testsets

def parse_configuration(node, base_config=None):
    """ Parse input config to configuration information """
    test_config = base_config
    if not test_config:
        test_config = TestConfig()

    node = lowercase_keys(flatten_dictionaries(node))  # Make it usable

    for key, value in node.items():
        if key == u'timeout':
            test_config.timeout = int(value)
        elif key == u'print_bodies':
            test_config.print_bodies = safe_to_bool(value)
        elif key == u'retries':
            test_config.retries = int(value)
        elif key == u'variable_binds':
            if not test_config.variable_binds:
                test_config.variable_binds = dict()
            test_config.variable_binds.update(flatten_dictionaries(value))
        elif key == u'generators':
            flat = flatten_dictionaries(value)
            gen_map = dict()
            for generator_name, generator_config in flat.items():
                gen = parse_generator(generator_config)
                gen_map[str(generator_name)] = gen
            test_config.generators = gen_map

    return test_config


class YamlReader(object):
    """Read yaml file"""
    def __init__(self, fname):
        self.logger = Logger(__name__).get_logger()
        self.fpath = '{}\\{}'.format(DefaultConfig().data_path, fname)

        self.yaml = self._read()

    def _read(self):
        with open(self.fpath, 'r') as f:
            y = [x for x in yaml.safe_load_all(f)]
            return y

    def get_cases(self):
        cases = list()
        for case in self.yaml:
            cases.append(self.get_case(case))
        return cases

    def get_case(self,case=None, case_num=1):
        if not case:
            case_data = self.yaml[case_num-1]
        else:
            case_data = case

        method_map = {'config': self.parse_config,
                      'classsetup': self.parse_classsetup,
                      'classteardown': self.parse_classteardown,
                      'setup': self.parse_setup,
                      'teardown': self.parse_teardown,
                      'test': self.parse_test
                      }

        for i in case_data:
            method_map[i.keys()[0]](i.values()[0])

    def parse_config(self, config):
        print 'config', config
        return config

    def parse_classsetup(self, classsetup):
        print 'class setup', classsetup


    def parse_classteardown(self, classteardown):
        print 'class teardown', classteardown
        pass

    def parse_setup(self, setup):
        print 'setup', setup
        pass

    def parse_teardown(self, teardown):
        print 'teardown', teardown
        pass

    def parse_test(self, test):
        print 'test', test
        pass


if __name__ == '__main__':
    y = YamlReader('TestCaseModel.yaml')
    # for set in y.yaml:
    #     for conf in set:
    #         print conf
    # a = {"a":1,"b":2}
    # print a.keys()[0],a.values()[0]
    y.get_cases()