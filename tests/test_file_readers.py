# -*- coding: utf-8 -*-

import unittest
import pprint
from src.utils.filereader.yaml_reader import YamlReader


class TestYamlReader(unittest.TestCase):

    def test_yaml_reader(self):
        ym = YamlReader('TestCaseModel.yaml')
        # pprint.pprint(ym.yaml)
        for node in ym.yaml:
            pprint.pprint(node)


if __name__ == '__main__':
    unittest.main(verbosity=0)