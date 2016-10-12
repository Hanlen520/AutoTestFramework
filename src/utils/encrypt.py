# -*- coding: utf-8 -*-
import hashlib
from src.utils.logger import Logger
from src.utils.config import Config, NoOptionError, NoSectionError, ConfigFileException
from src.utils.utils_exception import EncryptError

logger = Logger(__name__).get_logger()


class Encrypt:

    def __init__(self, conf=None, priv_key=None, salt=None):
        if conf:
            try:
                cf = Config(filename=conf)
            except ConfigFileException as e:
                logger.exception(e)
                raise

            try:
                self.priv_key = cf.get('encrypt', 'private_key')
            except (NoOptionError, NoSectionError):
                self.priv_key = None

            try:
                self.salt = cf.get('encrypt', 'salt')
            except (NoOptionError, NoSectionError):
                self.salt = None

            try:
                self.encrypt_way = cf.get('encrypt', 'encrypt')
            except (NoOptionError, NoSectionError):
                self.encrypt_way = None

        else:
            self.priv_key = priv_key
            self.salt = salt
            self.encrypt_way = 'MD5'

    def sign(self, sign_dict, priv=None):
        """传入待签名的字典，返回签名后字符串
        1.字典排序
        2.拼接，用&连接，最后拼接上私钥
        3.MD5加密"""
        if priv:
            self.priv_key = priv
        elif not self.priv_key:
            logger.error('未检查到私钥，请传入私钥！')
            raise EncryptError

        dict_keys = sign_dict.keys()
        dict_keys.sort()

        string = ''
        for key in dict_keys:
            if sign_dict[key] is None:
                pass
            else:
                string += '{0}={1}&'.format(key, sign_dict[key])
        string = string[0:len(string) - 1]
        string += self.priv_key
        string = string.replace(' ', '')

        hash_string = hashlib.md5()
        hash_string.update(string)
        return hash_string.hexdigest()

    def encrypt(self, befstr, salt=None, encryway=None):
        if salt:
            self.salt = salt
        elif not self.salt:
            logger.error('未检查到盐，请传入盐！')
            raise EncryptError

        if encryway:
            self.encrypt_way = encryway
        elif not self.encrypt_way:
            self.encrypt_way = 'MD5'

        befstr += self.salt
        if self.encrypt_way.upper() == 'MD5':
            hashstr = hashlib.md5()
        elif self.encrypt_way.upper() == 'SHA1':
            hashstr = hashlib.sha1()
        else:
            logger.error('请输入正确的加密方式，目前仅支持 MD5 或 SHA1')
            return None

        hashstr.update(befstr)
        return hashstr.hexdigest()

if __name__ == '__main__':
    print Encrypt(salt='111111').encrypt('100000307', encryway='MD5')
    print Encrypt(salt='1').encrypt('100000307111111', encryway='MD5')