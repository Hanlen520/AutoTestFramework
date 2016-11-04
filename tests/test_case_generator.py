# -*- coding: utf-8 -*-

import unittest
from src.utils.testutil.case_generator import parse_testsets
from src.utils.filereader.file_reader import FileReader


class TestParseTestsets(unittest.TestCase):

    def test_parse_testsets(self):
        ym = FileReader('TestCaseModel.yaml').read()
        testsets = parse_testsets('', ym.yaml)
        print 'Testsets:'
        print testsets
        for i in testsets:
            print 'Config:\t'
            print i.config
            for j in i.tests:
                print 'Test:\t'
                print j


if __name__ == '__main__':
    unittest.main(verbosity=0)
