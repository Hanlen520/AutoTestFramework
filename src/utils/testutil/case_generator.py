# -*- coding: utf-8 -*-
"""此类用来生成测试文件，从数据文件中读取测试用例，从xml中读取接口配置，组织到测试文件中。

一个接口是一个class，每一条测试用例是一个method。

"""

# todo Generator
import json
import yaml
from src.utils.filereader.file_reader import *
from src.utils.config import DefaultConfig, Config
from src.utils.logger import Logger
from src.utils.utils_exception import UnSupportFileType, NoSectionError, NoOptionError
from src.utils.filereader.parsing import *
from src.utils.filereader.generators import parse_generator
from src.utils.testutil.tests import RestTest


DATA_PATH = DefaultConfig().data_path

DEFAULT_TIMEOUT = 10
logger = Logger(__name__).get_logger()


class TestConfig(object):
    """ Configuration for a test run """
    # timeout = DEFAULT_TIMEOUT  # timeout of tests, in seconds
    print_bodies = False  # Print response bodies in all cases
    print_headers = False  # Print response bodies in all cases
    # retries = 0  # Retries on failures
    # test_parallel = False  # Allow parallel execution of tests in a test set, for speed?
    interactive = False
    verbose = False
    ssl_insecure = False
    # skip_term_colors = False  # Turn off output term colors

    headers = None
    test = None

    run = True

    # Binding and creation of generators
    variable_binds = None
    generators = None  # Map of generator name to generator function

    def __str__(self):
        return json.dumps(self, default=safe_to_json)


class TestSet(object):
    """ Encapsulates a set of tests and test configuration for them """
    tests = list()
    config = TestConfig()

    def __init__(self):
        self.config = TestConfig()
        self.tests = list()

    def __str__(self):
        return json.dumps(self, default=safe_to_json)


def read_file(path):
    """ Read an input into a file, doing necessary conversions around relative path handling """
    with open(path, "r") as f:
        string = f.read()
        f.close()
    return string


def read_test_file(path):
    """ Read test file at 'path' in YAML """
    teststruct = yaml.safe_load_all(read_file(path))
    return teststruct


# todo 修改解析testset、config等的方法


def parse_testsets(base_url, test_structure, vars=None):
    """ Convert a Python data structure read from validated YAML to a set of structured testsets
    The data structure is assumed to be a list of dictionaries, each of which describes:
        - a tests (test structure)
        - a simple test (just a URL, and a minimal test is created)
        - or overall test configuration for this testset

    This returns a list of testsets, corresponding to imported testsets and in-line multi-document sets
    """


    test_config = TestConfig()
    testsets = list()

    if vars and isinstance(vars, dict):
        test_config.variable_binds = vars

    # returns a testconfig and collection of tests
    for node in test_structure:  # Iterate through lists of test and configuration elements
        tests_out = list()
        # print node
        if isinstance(node, dict):  # Each config element is a miniature key-value dictionary
            node = lowercase_keys(node)
            for key in node:
                if key == u'config':
                    test_config = parse_configuration(node[key], base_config=test_config)
                elif key == u'url':  # Simple test, just a GET to a URL
                    mytest = RestTest()
                    val = node[key]
                    assert isinstance(val, basestring)
                    mytest.url = base_url + val
                    tests_out.append(mytest)
                elif key == u'test':  # Complex test with additional parameters
                    child = node[key]
                    mytest = RestTest.parse_test(base_url, child)
                    tests_out.append(mytest)
        testset = TestSet()
        testset.tests = tests_out
        testset.config = test_config
        testsets.append(testset)
    return testsets


def parse_configuration(node, base_config=None):
    """ Parse input config to configuration information """
    test_config = base_config
    if not test_config:
        test_config = TestConfig()

    node = lowercase_keys(flatten_dictionaries(node))  # Make it usable

    for key, value in node.items():
        if key == u'print_bodies':
            test_config.print_bodies = safe_to_bool(value)
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
        elif key == u'testset':
            test_config.test = value
        elif key == u'run':
            test_config.run = safe_to_bool(value)
        elif key == u'headers':
            test_config.headers = safe_to_json(flatten_dictionaries(value))

    return test_config


def parse_headers(header_string):
    """ Parse a header-string into individual headers
        Implementation based on: http://stackoverflow.com/a/5955949/95122
        Note that headers are a list of (key, value) since duplicate headers are allowed

        NEW NOTE: keys & values are unicode strings, but can only contain ISO-8859-1 characters
    """
    # First line is request line, strip it out
    if not header_string:
        return list()
    request, headers = header_string.split('\r\n', 1)
    if not headers:
        return list()

    from email import message_from_string
    header_msg = message_from_string(headers)
    # Note: HTTP headers are *case-insensitive* per RFC 2616
    return [(k.lower(), v) for k, v in header_msg.items()]


class Generator(object):
    """测试生成器基本类"""
    def __init__(self, project):
        """

        :param project: 项目名称
        """
        self.proj_name = project

        self.conf_file = 'config_{}.ini'.format(self.proj_name)
        self.cf = Config(self.conf_file)

        self.test_file_name = 'test_{}.py'.format(self.proj_name)

    import_string = "# -*- coding: utf-8 -*-\nimport unittest\nimport json\n"
    class_string = "\nclass Test{}(unittest.TestCase):\n"
    tab = "    "
    setup_string = "\n    def setUp(self):\n"
    teardown_string = "\n    def tearDown(self):\n"
    class_setup_string = "\n    def setUpClass(cls):\n"
    class_teardown_string = "\n    def tearDownClass(cls):\n"
    test_method_string = "\n    def test_{}_{}(self):\n"


class InterfaceTestCaseGenerator(Generator):
    """测试类生成器"""
    logger = Logger(__name__).get_logger()

    def __init__(self, project):
        """初始化生成器，传入项目名称，获取相应配置文件、数据文件、接口文件"""
        Generator.__init__(self, project)

        self.case_file = self.cf.get('file', 'interfaces')
        self.case_file_type = self.case_file.split('.').pop()

        if self.case_file_type in ['yaml', 'yml']:
            self.interface_reader = YamlReader(self.case_file)
        elif self.case_file_type == 'xml':
            self.interface_reader = XMLReader(self.case_file)
        else:
            self.logger.exception(UnSupportFileType(u'不支持的用例文件类型，请检查配置文件！'))

        try:
            self.encrypt = self.cf.get('encrypt', 'encrypt')
        except (NoSectionError or NoOptionError):
            self.encrypt = False
        if self.encrypt:
            self.private_key = self.cf.get('encrypt', 'private_key')
            self.salt = self.cf.get('encrypt', 'salt')

    def generate(self):
        with open(self.test_file, 'wb') as test_file:
            test_file.write(self.import_string)
            for tag in self.tags:
                # interface = self.interface_reader.get_url(tag)

                class_string = self.get_class(tag)
                test_file.write(class_string)

                test_file.write('\n\n\n')

    @property
    def import_string(self):
        import_string = """# -*- coding: utf-8 -*-\nimport unittest\nimport json\n"""
        rest_flag = webservice_flag = socket_flag = 0
        for tag in self.tags:
            interface_type = self.interface_reader.get_type(tag).lower()
            if interface_type in ['rest', 'restful', 'http']:
                rest_flag = 1
            elif interface_type == 'webservice':
                webservice_flag = 1
            elif interface_type in ['tcp', 'socket']:
                socket_flag = 1
            else:
                self.logger.error(u'没有找到合适的接口类型')
        if rest_flag:
            import_string += 'import requests\n'
        if webservice_flag:
            import_string += 'import suds\n'
        if socket_flag:
            import_string += 'import socket\n'
        import_string += 'from src.utils.logger import Logger\n\n'
        return import_string

    def get_class(self, tag):
        data_file = self.interface_reader.get_file(tag)
        sheet = self.interface_reader.get_sheet(tag)
        excel_reader = ExcelReader(data_file, sheet=sheet)

        interface_type = self.interface_reader.get_type(tag).lower()

        class_string = 'class Test%s(unittest.TestCase):\n\n' % tag

        # todo: rest webservice socket

        if interface_type in ['rest', 'restful', 'http']:
            setup_string = self.get_rest_setup(tag)
            cases_string = ''
            teardown_string = self.get_rest_teardown(tag)

            for num, case in enumerate(excel_reader.data):
                case_string = self.get_rest_test(tag, num, case)
                cases_string += case_string

            class_string += setup_string + teardown_string + cases_string
        return class_string

    def get_rest_setup(self, tag):
        setup_string = """    def setUp(self):\n        session = requests.session()\n\n"""
        return setup_string

    def get_rest_teardown(self, tag):
        teardown_string = """    def tearDown(self):\n        pass\n\n"""
        return teardown_string

    def get_rest_test(self, tag, num, case):
        method = self.interface_reader.get_method(tag)
        interface_url = self.interface_reader.get_url(tag)
        test_string = """    def test_%s_%d(self):\n        pass\n\n""" % (tag, num)
        return test_string

    def get_setup(self, interface):
        pass

    def get_test(self, interface):
        pass

    def get_teardown(self, interface):
        pass


if __name__ == '__main__':
    # g = InterfaceTestCaseGenerator('zhigou')
    # print g.interfaces
    # g.generate()
    # print g.import_string
    ym = FileReader('TestCaseModel.yaml').read()
    for i in parse_testsets('', ym.yaml):
        print i.config
        for j in i.tests:
            print j
