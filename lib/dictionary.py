from config.config import *
config = getConfig()
prefixes = [] if config['prefixes'] == "[]" else [i for i in config['prefixes'][1:-1].split(',')]
suffixes = [] if config['suffixes'] == "[]" else [i for i in config['suffixes'][1:-1].split(',')]
extensions = [] if config['extensions'] == "[]" else [i for i in config['extensions'][1:-1].split(',')]

from lib.decorators import locked
from lib.utils import FileUtils, lstrip_once

class OrderedSet():
    def __init__(self, items=[]):
        self._data = dict()

        for item in items:
            self._data[item] = None

    def __contains__(self, item):
        return item in self._data

    def __eq__(self, other):
        return self._data.keys() == other._data.keys()

    def __iter__(self):
        return iter(list(self._data))

    def __len__(self):
        return len(self._data)

    def add(self, item):
        self._data[item] = None

    def clear(self):
        self._data.clear()

    def discard(self, item):
        self._data.pop(item, None)

    def pop(self):
        self._data.popitem()

    def remove(self, item):
        del self._data[item]

    def update(self, items):
        for item in items:
            self.add(item)

class Dictionary:
    def __init__(self, **kwargs):
        self._index = 0
        self._items = self.generate(**kwargs)

    @locked
    def __next__(self):
        try:
            path = self._items[self._index]
        except IndexError:
            raise StopIteration
        self._index += 1
        return path

    @property
    def index(self):
        return self._index

    def __contains__(self, item):
        return item in self._items

    def __getstate__(self):
        return (self._items, self._index)

    def __setstate__(self, state):
        self._items, self._index = state

    def __iter__(self):
        return iter(self._items)

    def __len__(self):
        return len(self._items)

    def generate(self, files=[]):
        wordlist = OrderedSet()
        re_ext_tag = re.compile(EXTENSION_TAG, re.IGNORECASE)

        for dict_file in files:
            for line in FileUtils.get_lines(dict_file):
                line = lstrip_once(line, "/")
                if not self.is_valid(line):
                    continue
                if EXTENSION_TAG in line.lower():
                    for extension in extensions:
                        newline = re_ext_tag.sub(extension, line)
                        wordlist.add(newline)
                else:
                    wordlist.add(line)

        altered_wordlist = OrderedSet()
        for path in wordlist:
            for pref in prefixes:
                if (not path.startswith(("/", pref))):
                    altered_wordlist.add(pref + path)
            for suff in suffixes:
                if (not path.endswith(("/", suff)) and "?" not in path and "#" not in path):
                    altered_wordlist.add(path + suff)

        if altered_wordlist:
            wordlist = altered_wordlist

        return list(wordlist)

    def is_valid(self, path):
        if not path or path.startswith("#"):
            return False
        return True

    def reset(self):
        self._index = 0
