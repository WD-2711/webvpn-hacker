from config.config import *
config = getConfig()
prefixes = [] if config['prefixes'] == "[]" else [i for i in config['prefixes'][1:-1].split(',')]
suffixes = [] if config['suffixes'] == "[]" else [i for i in config['suffixes'][1:-1].split(',')]
extensions = [] if config['extensions'] == "[]" else [i for i in config['extensions'][1:-1].split(',')]
thread_count = config['thread_count']
crawl = False if config['crawl'] == "False" else True

from lib.scanner import Scanner
from lib.crawl import Crawler
from lib.utils import clean_path

class Fuzzer:
    def __init__(self, requester, dictionary, **kwargs):
        self._threads = []
        self._scanned = set()
        self._requester = requester
        self._dictionary = dictionary
        self._play_event = threading.Event()
        self._quit_event = threading.Event()
        self._pause_semaphore = threading.Semaphore(0)
        self._base_path = None
        self.exc = None
        self.match_callbacks = kwargs.get("match_callbacks", [])
        self.not_found_callbacks = kwargs.get("not_found_callbacks", [])
        self.error_callbacks = kwargs.get("error_callbacks", [])

    def setup_scanners(self):
        self.scanners = {"default": {}, "prefixes": {}, "suffixes": {},}

        # Default scanners (wildcard testers)
        self.scanners["default"].update({
            "index": Scanner(self._requester, path=self._base_path),
            "random": Scanner(self._requester, path=self._base_path + WILDCARD_TEST_POINT_MARKER),
        })

        for prefix in prefixes + DEFAULT_TEST_PREFIXES:
            self.scanners["prefixes"][prefix] = Scanner(
                self._requester, tested=self.scanners,
                path=f"{self._base_path}{prefix}{WILDCARD_TEST_POINT_MARKER}",
            )

        for suffix in suffixes + DEFAULT_TEST_SUFFIXES:
            self.scanners["suffixes"][suffix] = Scanner(
                self._requester, tested=self.scanners,
                path=f"{self._base_path}{WILDCARD_TEST_POINT_MARKER}{suffix}",
            )

        for extension in extensions:
            if "." + extension not in self.scanners["suffixes"]:
                self.scanners["suffixes"]["." + extension] = Scanner(
                    self._requester, tested=self.scanners,
                    path=f"{self._base_path}{WILDCARD_TEST_POINT_MARKER}.{extension}",
                )

    def setup_threads(self):
        if self._threads:
            self._threads = []

        for _ in range(thread_count):
            new_thread = threading.Thread(target=self.thread_proc)
            new_thread.daemon = True
            self._threads.append(new_thread)

    def get_scanners_for(self, path):
        path = clean_path(path)

        for prefix in self.scanners["prefixes"]:
            if path.startswith(prefix):
                yield self.scanners["prefixes"][prefix]

        for suffix in self.scanners["suffixes"]:
            if path.endswith(suffix):
                yield self.scanners["suffixes"][suffix]

        for scanner in self.scanners["default"].values():
            yield scanner

    def start(self):
        self.setup_scanners()
        self.setup_threads()
        self.play()

        for thread in self._threads:
            thread.start()

    def is_finished(self):
        if self.exc:
            raise self.exc

        for thread in self._threads:
            if thread.is_alive():
                return False

        return True

    def play(self):
        self._play_event.set()

    def scan(self, path, scanners):
        if path in self._scanned:
            return
        else:
            self._scanned.add(path)

        response = self._requester.request(path)

        for tester in scanners:
            if not tester.check(path, response):
                for callback in self.not_found_callbacks:
                    callback(response)
                return

        for callback in self.match_callbacks:
            callback(response)

        if crawl:
            for path_ in Crawler.crawl(response):
                if self._dictionary.is_valid(path_):
                    self.scan(path_, self.get_scanners_for(path_))

    def set_base_path(self, path):
        self._base_path = path

    def thread_proc(self):
        while True:
            try:
                path = next(self._dictionary)
                scanners = self.get_scanners_for(path)
                self.scan(self._base_path + path, scanners)
            except StopIteration:
                break

            if not self._play_event.is_set():
                self._pause_semaphore.release()
                self._play_event.wait()

