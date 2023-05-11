from config.config import *
config = getConfig()

from lib.utils import clean_path, parse_path, merge_path

def _filter(paths):
    return {clean_path(path) for path in paths if not path.endswith(MEDIA_EXTENSIONS)}

class Crawler:
    @classmethod
    def crawl(cls, response):
        scope = "/".join(response.url.split("/")[:3]) + "/"

        if "text/html" in response.headers.get("content-type", ""):
            return cls.html_crawl(response.url, scope, response.content)
        elif response.path == "robots.txt":
            return cls.robots_crawl(response.url, scope, response.content)
        else:
            return cls.text_crawl(response.url, scope, response.content)

    @staticmethod
    @lru_cache(maxsize=None)
    def text_crawl(url, scope, content):
        results = []
        regex = re.escape(scope) + "[a-zA-Z0-9-._~!$&*+,;=:@?%]+"

        for match in re.findall(regex, content):
            results.append(match[len(scope):])

        return _filter(results)

    @staticmethod
    @lru_cache(maxsize=None)
    def html_crawl(url, scope, content):
        results = []
        soup = BeautifulSoup(content, 'html.parser')

        for tag in CRAWL_TAGS:
            for found in soup.find_all(tag):
                for attr in CRAWL_ATTRIBUTES:
                    value = found.get(attr)

                    if not value:
                        continue
                    if value.startswith("/"):
                        results.append(value[1:])
                    elif value.startswith(scope):
                        results.append(value[len(scope):])
                    elif not re.search(r"^[a-z]{2,}:", value):
                        new_url = merge_path(url, value)
                        results.append(parse_path(new_url))

        return _filter(results)

    @staticmethod
    @lru_cache(maxsize=None)
    def robots_crawl(url, scope, content):
        return _filter(re.findall(r"(?:Allow|Disallow): /(.*)", content))
