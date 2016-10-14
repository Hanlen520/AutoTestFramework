# -*- coding: utf-8 -*-

import yaml
from src.utils.config import DefaultConfig
from src.utils.filereader.parsing import *
from src.utils.logger import Logger


logger = Logger(__name__).get_logger()
# todo 组织成YamlReader类


class YamlReader(object):
    """Read yaml file"""
    def __init__(self, fname):
        self.fpath = '{}\\{}'.format(DefaultConfig().data_path, fname)
        self._yaml = None

    @property
    def yaml(self):
        if not self._yaml:
            self._yaml = self._read()
        return self._yaml

    def _read(self):
        logger.info('read yaml file {}'.format(self.fpath))
        with open(self.fpath, 'r') as f:
            al = yaml.safe_load_all(f)
            y = [flatten_dictionaries(x) for x in al]
            return y


if __name__ == '__main__':
    ym = YamlReader('TestCaseModel.yaml')
    # print ym.yaml
    # for i in parse_testsets('', ym.yaml):
    #     print i
