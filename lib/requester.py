from config.config import *
config = getConfig()
thread_count = config['thread_count']
max_retries = config['max_retries']
http_method = config['http_method']
request_data = None if config['request_data'] == "None" else None
follow_redirects = False if config['allow_redirects'] == "False" else True

from lib.utils import clean_path, parse_path, is_binary

class Response:
    def __init__(self, response):
        self.url = response.url
        self.full_path = parse_path(response.url)
        self.path = clean_path(self.full_path)
        self.status = response.status_code
        self.headers = response.headers
        self.redirect = self.headers.get("location") or ""
        self.history = [res.url for res in response.history]
        self.content = ""
        self.body = b""

        for chunk in response.iter_content(chunk_size=1024*1024):
            self.body += chunk

            if len(self.body) >= 80*1024*1024 or (
                "content-length" in self.headers and is_binary(self.body)
            ):
                break

        if not is_binary(self.body):
            self.content = self.body.decode(response.encoding or "utf-8", errors="ignore")

    @property
    def type(self):
        if "content-type" in self.headers:
            return self.headers.get("content-type").split(";")[0]

        return "__unknown__"

    @property
    def length(self):
        try:
            return int(self.headers.get("content-length"))
        except TypeError:
            return len(self.body)

    def __hash__(self):
        return hash(self.body)

    def __eq__(self, other):
        return (self.status, self.body, self.redirect) == (
            other.status,
            other.body,
            other.redirect,
        )

class Requester:
    def __init__(self):
        self._url = None
        self._proxy_cred = None
        self._rate = 0
        self.headers = DEFAULT_HEADERS
        self.agents = []
        self.session = requests.Session()
        self.session.verify = False

        for scheme in ("http://", "https://"):
            self.session.mount(scheme, HTTPAdapter(max_retries=0, pool_maxsize=thread_count))

    def set_url(self, url):
        self._url = url

    def set_header(self, key, value):
        self.headers[key] = value.lstrip()

    def request(self, path):

        url = self._url + path

        for _ in range(max_retries + 1):
            request = requests.Request(
                http_method,
                url,
                headers=self.headers,
                data=request_data,
            )
            prepped = self.session.prepare_request(request)
            prepped.url = url

            response = self.session.send(
                prepped,
                allow_redirects=follow_redirects,
                timeout=7.5,
                stream=True,
            )
            response = Response(response)
            return response
