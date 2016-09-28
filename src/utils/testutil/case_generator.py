# -*- coding: utf-8 -*-
"""此类用来生成测试文件，从数据文件中读取测试用例，从xml中读取接口配置，组织到测试文件中。

一个接口是一个class，每一条测试用例是一个method。

"""

# todo Generator
from src.utils.filereader.excel_reader import ExcelReader
from src.utils.filereader.xml_reader import XMLReader
from src.utils.filereader.yaml_reader import YamlReader
from src.utils.config import DefaultConfig, Config
from src.utils.logger import Logger
from src.utils.utils_exception import UnSupportFileType, NoSectionError, NoOptionError


DATA_PATH = DefaultConfig().data_path


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
    g = InterfaceTestCaseGenerator('zhigou')
    # print g.interfaces
    g.generate()
    # print g.import_string









