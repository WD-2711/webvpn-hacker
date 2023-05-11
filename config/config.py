#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
# @Time  : 2023/05/07 15:39:34
# @Author: wd-2711
'''


# dependent library
import os
import gc
import re
import time
import ssl
import socket
import threading
import requests
import random
import string
import difflib

from bs4 import BeautifulSoup
from functools import lru_cache
from requests.adapters import HTTPAdapter
from requests.packages import urllib3
from Crypto.Cipher import AES
from urllib.parse import urlparse, urljoin, unquote
from binascii import hexlify, unhexlify
from configparser import SafeConfigParser

# Disable InsecureRequestWarning from urllib3
urllib3.disable_warnings(urllib3.exceptions.SecurityWarning)

# config
config_file = './config/config.ini'
def getConfig():
    if not os.path.exists(config_file):
        print("[+] config file not exist.")
        exit()
    parser = SafeConfigParser()
    parser.read(config_file, encoding = 'utf-8')
    strings = [(k, str(v)) for k, v in parser.items('strings')]
    ints = [(k, int(v)) for k, v in parser.items('ints')]
    return dict(strings + ints)

STANDARD_PORTS = {"http": 80, "https": 443}

WILDCARD_TEST_POINT_MARKER = "__WILDCARD_POINT__"

DEFAULT_TEST_PREFIXES = [".",]

DEFAULT_TEST_SUFFIXES = ["/",]

EXTENSION_TAG = "%ext%"

REFLECTED_PATH_MARKER = "__REFLECTED_PATH__"

TEXT_CHARS = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7F})

MEDIA_EXTENSIONS = ("webm", "mkv", "avi", "ts", "mov", "qt", "amv", "mp4", "m4p", "m4v", "mp3", "swf", "mpg", "mpeg", "jpg", "jpeg", "pjpeg", "png", "woff", "svg", "webp", "bmp", "pdf", "wav", "vtt")

CRAWL_TAGS = ["a", "area", "base", "blockquote", "button", "embed", "form", "frame", "frameset", "html", "iframe", "input", "ins", "noframes", "object", "q", "script", "source"]

CRAWL_ATTRIBUTES = ["action", "cite", "data", "formaction", "href", "longdesc", "poster", "src", "srcset", "xmlns"]

DEFAULT_HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
    "accept": "*/*",
    "accept-encoding": "*",
    "keep-alive": "timeout=15, max=1000",
    "cache-control": "max-age=0",
    "cookie": "show_vpn=0;show_faq=0;wengine_vpn_ticketwebvpn_bit_edu_cn=002079babc2371fb;refresh=1"
}

BANNER = f"""
               _                                                                
              | |                                                               
 __      _____| |____   ___ __  _ __ ______ ___  ___ __ _ _ __  _ __   ___ _ __ 
 \ \ /\ / / _ \ '_ \ \ / / '_ \| '_ \______/ __|/ __/ _` | '_ \| '_ \ / _ \ '__|
  \ V  V /  __/ |_) \ V /| |_) | | | |     \__ \ (_| (_| | | | | | | |  __/ |   
   \_/\_/ \___|_.__/ \_/ | .__/|_| |_|     |___/\___\__,_|_| |_|_| |_|\___|_|   v1.0.0
                         | |                                                    
                         |_| 
"""