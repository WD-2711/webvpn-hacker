#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
# @Time  : 2023/05/07 15:35:37
# @Author: wd-2711
# @Ref   : https://github.com/ESWZY/webvpn-dlut
'''

from config.config import *
config = getConfig()
institution = config['institution']
key_ = config['key_'].encode('utf-8')
iv_  = config['iv_'].encode('utf-8')

def get_ciphertext(plaintext, key = key_, cfb_iv = iv_, size = 128):
    '''From plantext hostname to ciphertext'''
    
    message = plaintext.encode('utf-8')
    
    cfb_cipher_encrypt = AES.new(key, AES.MODE_CFB, cfb_iv, segment_size = size)       # Must include segment_size
    mid = cfb_cipher_encrypt.encrypt(message)

    return hexlify(mid).decode()

def get_plaintext(ciphertext, key = key_, cfb_iv = iv_, size = 128):
    '''From ciphertext hostname to plaintext'''
    
    message = unhexlify(ciphertext.encode('utf-8'))
    
    cfb_cipher_decrypt = AES.new(key, AES.MODE_CFB, cfb_iv, segment_size = size)
    cfb_msg_decrypt = cfb_cipher_decrypt.decrypt(message).decode('utf-8')
    
    return cfb_msg_decrypt

    return message

def get_vpn_url(url):
    '''From ordinary url to webVPN url'''

    parts = url.split('://')
    pro = parts[0]
    pro_alter = "http" if pro == "https" else "https"
    add = parts[1]
    
    hosts = add.split('/')
    domain = hosts[0].split(':')[0]
    port = '-' + hosts[0].split(':')[1] if ":" in hosts[0] else ''
    cph = get_ciphertext(domain)
    fold = '/'.join(hosts[1:])

    key = hexlify(iv_).decode('utf-8')
    
    return ['https://' + institution + '/' + pro + port + '/' + key + cph + '/' + fold, 'https://' + institution + '/' + pro_alter + port + '/' + key + cph + '/' + fold]

def get_ordinary_url(url):
    '''From webVPN url to ordinary url'''

    parts = url.split('/')
    pro = parts[3]
    if "-" in pro:
        port = pro.split("-")[1]
        pro = pro.split("-")[0]
    else:
        port = ""
    key_cph = parts[4]
    
    if key_cph[:16] == hexlify(iv_).decode('utf-8'):
        print(key_cph[:32])
        return None
    else:
        hostname = get_plaintext(key_cph[32:])
        fold = '/'.join(parts[5:])
        if port == "":
            return pro + "://" + hostname + '/' + fold
        else:
            return pro + "://" + hostname + ":" + port + '/' + fold

def lstrip_once(string, pattern):
    if string.startswith(pattern):
        return string[len(pattern):]

    return string

def detect_scheme(host, port):
    if not port:
        raise ValueError
    socket_timeout = 6
    s = socket.socket()
    s.settimeout(socket_timeout)
    conn = ssl.SSLContext().wrap_socket(s)

    try:
        conn.connect((host, port))
        conn.close()
        return "https"
    except Exception:
        return "http"

def clean_path(path):
    path = path.split("#")[0]
    path = path.split("?")[0]
    return path

def parse_path(value):
    try:
        scheme, url = value.split("//", 1)
        return "/".join(url.split("/")[1:])
    except Exception:
        return lstrip_once(value, "/")

def is_binary(bytes):
    return bool(bytes.translate(None, TEXT_CHARS))

class File:
    def __init__(self, *path_components):
        self._path = FileUtils.build_path(*path_components)

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        raise NotImplementedError

    def is_valid(self):
        return FileUtils.is_file(self.path)

    def exists(self):
        return FileUtils.exists(self.path)

    def can_read(self):
        return FileUtils.can_read(self.path)

    def can_write(self):
        return FileUtils.can_write(self.path)

    def read(self):
        return FileUtils.read(self.path)

    def get_lines(self):
        return FileUtils.get_lines(self.path)

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        pass

class FileUtils:
    @staticmethod
    def build_path(*path_components):
        if path_components:
            path = os.path.join(*path_components)
        else:
            path = ""

        return path

    @staticmethod
    def get_abs_path(file_name):
        return os.path.abspath(file_name)

    @staticmethod
    def exists(file_name):
        return os.access(file_name, os.F_OK)

    @staticmethod
    def can_read(file_name):
        try:
            with open(file_name):
                pass
        except IOError:
            return False

        return True

    @classmethod
    def can_write(cls, path):
        while not cls.exists(path):
            path = cls.parent(path)

        return os.access(path, os.W_OK)

    @staticmethod
    def read(file_name):
        return open(file_name, "r").read()

    @classmethod
    def get_files(cls, directory):
        files = []

        for path in os.listdir(directory):
            path = os.path.join(directory, path)
            if cls.is_dir(path):
                files.extend(cls.get_files(path))
            else:
                files.append(path)

        return files

    @staticmethod
    def get_lines(file_name):
        with open(file_name, "r", errors="replace") as fd:
            return fd.read().splitlines()

    @staticmethod
    def is_dir(path):
        return os.path.isdir(path)

    @staticmethod
    def is_file(path):
        return os.path.isfile(path)

    @staticmethod
    def parent(path, depth=1):
        for _ in range(depth):
            path = os.path.dirname(path)

        return path

    @classmethod
    def create_dir(cls, directory):
        if not cls.exists(directory):
            os.makedirs(directory)

    @staticmethod
    def write_lines(file_name, lines, overwrite=False):
        if isinstance(lines, list):
            lines = os.linesep.join(lines)
        with open(file_name, "w" if overwrite else "a") as f:
            f.writelines(lines)

def merge_path(url, path):
    parts = url.split("/")
    path = urljoin("/", path).lstrip("/")
    parts[-1] = path
    return "/".join(parts)

def rand_string(n, omit=None):
    seq = string.ascii_lowercase + string.ascii_uppercase + string.digits
    if omit:
        seq = list(set(seq) - set(omit))
    return "".join(random.choice(seq) for _ in range(n))

class DynamicContentParser:
    def __init__(self, content1, content2):
        self._static_patterns = None
        self._differ = difflib.Differ()
        self._is_static = content1 == content2
        self._base_content = content1

        if not self._is_static:
            self._static_patterns = self.get_static_patterns(
                self._differ.compare(content1.split(), content2.split())
            )

    def compare_to(self, content):
        """
        DynamicContentParser.compare_to() workflow

          1. Check if the wildcard response is static or not, if yes, compare 2 responses
          2. If it's not static, get static patterns (splitting by space) in both responses
            and check if they match
          3. In some rare cases, checking static patterns fails, so make a final confirmation
            if the similarity ratio of 2 responses is not high enough to prove they are the same
        """

        if self._is_static and content == self._base_content:
            return True

        diff = self._differ.compare(self._base_content.split(), content.split())
        static_patterns_are_matched = self._static_patterns == self.get_static_patterns(diff)
        match_ratio = difflib.SequenceMatcher(None, self._base_content, content).ratio()
        return static_patterns_are_matched or match_ratio > 0.98

    @staticmethod
    def get_static_patterns(patterns):
        # difflib.Differ.compare returns something like below:
        # ["  str1", "- str2", "+ str3", "  str4"]
        #
        # Get only stable patterns in the contents
        return [pattern for pattern in patterns if pattern.startswith("  ")]

def generate_matching_regex(string1, string2):
    start = "^"
    end = "$"

    for char1, char2 in zip(string1, string2):
        if char1 != char2:
            start += ".*"
            break

        start += re.escape(char1)

    if start.endswith(".*"):
        for char1, char2 in zip(string1[::-1], string2[::-1]):
            if char1 != char2:
                break

            end = re.escape(char1) + end

    return start + end

if __name__ == '__main__':
    #print(getCiphertext('xueshu.baidu.com'))
    #print(getPlaintext('e7e056d2253161546b468aa395'))

    url = 'https://kns.cnki.net/KCMS/detail/detail.aspx?dbcode=CJFQ&dbname=CJFD2007&filename=JEXK200702000&uid=WEEvREcwSlJHSldRa1FhcTdnTnhXY20wTWhLQWVGdmJFOTcvMFFDWDBycz0=$9A4hF_YAuvQ5obgVAqNKPCYcEjKensW4IQMovwHtwkF4VYPoHbKxJw!!&v=MTYzNjU3cWZaT2RuRkNuaFZMN0tMeWpUWmJHNEh0Yk1yWTlGWklSOGVYMUx1eFlTN0RoMVQzcVRyV00xRnJDVVI='
    url = 'http://10.0.8.207/?wrdrecordvisit=1683437814000'
    url = 'http://10.0.0.55:8138/srun_portal_pc?ac_id=8&srun_wait=1&theme=bit'
    print('From ordinary url: \n' + get_vpn_url(url))

    VPNUrl = 'https://' + institution + '/https/77726476706e69737468656265737421fbf952d2243e635930068cb8/KCMS/detail/detail.aspx?dbcode=CJFQ&dbname=CJFD2007&filename=JEXK200702000&uid=WEEvREcwSlJHSldRa1FhcTdnTnhXY20wTWhLQWVGdmJFOTcvMFFDWDBycz0=$9A4hF_YAuvQ5obgVAqNKPCYcEjKensW4IQMovwHtwkF4VYPoHbKxJw!!&v=MTYzNjU3cWZaT2RuRkNuaFZMN0tMeWpUWmJHNEh0Yk1yWTlGWklSOGVYMUx1eFlTN0RoMVQzcVRyV00xRnJDVVI='
    VPNUrl = 'https://' + institution + '/http-8138/77726476706e69737468656265737421a1a70fcc696626022e5f/day.php?year=2023&month=05&day=07&area=1&room=2'
    print('\nFrom webVPN url: \n' + get_ordinary_url(VPNUrl))

    
