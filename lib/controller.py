from lib.fuzzer import Fuzzer
from lib.requester import Requester
from lib.dictionary import Dictionary
from lib.decorators import locked
from lib.utils import lstrip_once, detect_scheme, parse_path, clean_path, get_vpn_url
from lib.view import view

from config.config import *
config = getConfig()
wordlists_path = [i for i in config['wordlists'][1:-1].split(",")]
urls = []
for i in config['scan_urls'][1:-1].split(","):
    urls += get_vpn_url(i.strip())
recursion_status_codes = [i for i in range(int(config['recursion_status_codes'].split("-")[0]), int(config['recursion_status_codes'].split("-")[1]))]
recursion_depth = config['recursion_depth']

class Controller:
    def __init__(self):
        self.setup()
        self.run()

    def setup(self):
        self.requester = Requester()
        self.dictionary = Dictionary(files=wordlists_path)
        self.results = []
        self.passed_urls = set()
        self.start_time = time.time()
        self.directories = []
        self.report = None
        self.batch = False
        self.jobs_processed = 0
        self.errors = 0
        self.consecutive_errors = 0
        view("init", [str(len(self.dictionary))])

    def run(self):
        match_callbacks = [self.match_callback, self.reset_consecutive_errors]
        not_found_callbacks = [self.reset_consecutive_errors]
        error_callbacks = [self.raise_error]
        while urls:
            url = urls[0]
            self.fuzzer = Fuzzer(self.requester, self.dictionary, match_callbacks=match_callbacks, not_found_callbacks=not_found_callbacks, error_callbacks=error_callbacks,)
            self.set_target(url)
            if not self.directories:
                self.add_directory(self.base_path)
            view("target", [self.url])
            self.start()
            urls.pop(0)

    def start(self):
        while self.directories:
            gc.collect()
            current_directory = self.directories[0]
            view("start", [current_directory])
            self.fuzzer.set_base_path(current_directory)
            self.fuzzer.start()
            self.process()
            self.dictionary.reset()
            self.directories.pop(0)
            self.jobs_processed += 1

    def set_target(self, url):
        if "://" not in url:
            url = f'__unknown__://{url}'
        if not url.endswith("/"):
            url += "/"

        parsed = urlparse(url)
        self.base_path = lstrip_once(parsed.path, "/")
        host = parsed.netloc.split(":")[0]
        try:
            port = int(parsed.netloc.split(":")[1])
        except IndexError:
            port = STANDARD_PORTS.get(parsed.scheme, None)

        try:
            scheme = (parsed.scheme if parsed.scheme != "__unknown__" else detect_scheme(host, port))
        except ValueError:
            scheme = detect_scheme(host, 443)
            port = STANDARD_PORTS[scheme]

        self.url = f"{scheme}://{host}"
        if port != STANDARD_PORTS[scheme]:
            self.url += f":{port}"

        self.url += "/"
        self.requester.set_url(self.url)

    def reset_consecutive_errors(self, response):
        self.consecutive_errors = 0

    def match_callback(self, response):
        view("scanning", [response])
        if response.status in recursion_status_codes:
            if response.redirect:
                new_path = clean_path(parse_path(response.redirect))
                added_to_queue = self.recur_for_redirect(response.path, new_path)
            elif len(response.history):
                old_path = clean_path(parse_path(response.history[0]))
                added_to_queue = self.recur_for_redirect(old_path, response.path)
            else:
                added_to_queue = self.recur(response.path)

    def raise_error(self, exception):
        self.errors += 1
        self.consecutive_errors += 1

    def process(self):
        while True:
            while not self.fuzzer.is_finished():
                pass
            break

    def add_directory(self, path):
        url = self.url + path

        if (path.count("/") - self.base_path.count("/") > recursion_depth > 0 or url in self.passed_urls):
            return
        self.directories.append(path)
        self.passed_urls.add(url)

    @locked
    def recur(self, path):
        dirs_count = len(self.directories)
        path = clean_path(path)

        if (path.endswith("/") and re.search(r"\w+([.][a-zA-Z0-9]{2,5}){1,3}~?$", path[:-1]) is None):
            self.add_directory(path)

        return self.directories[dirs_count:]

    def recur_for_redirect(self, path, redirect_path):
        if redirect_path == path + "/":
            return self.recur(redirect_path)

        return []
