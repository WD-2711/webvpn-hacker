from config.config import *
config = getConfig()

from lib.utils import rand_string, clean_path, generate_matching_regex, DynamicContentParser

class Scanner:
    def __init__(self, requester, **kwargs):
        self.path = kwargs.get("path", "")
        self.tested = kwargs.get("tested", [])
        self.context = kwargs.get("context", "all cases")
        self.requester = requester
        self.response = None
        self.wildcard_redirect_regex = None
        self.setup()

    def setup(self):
        first_path = self.path.replace(WILDCARD_TEST_POINT_MARKER, rand_string(6),)
        first_response = self.requester.request(first_path)
        self.response = first_response

        duplicate = self.get_duplicate(first_response)

        if duplicate:
            self.content_parser = duplicate.content_parser
            self.wildcard_redirect_regex = duplicate.wildcard_redirect_regex
            return

        second_path = self.path.replace(WILDCARD_TEST_POINT_MARKER, rand_string(6, omit=first_path),)
        second_response = self.requester.request(second_path)

        if first_response.redirect and second_response.redirect:
            self.wildcard_redirect_regex = self.generate_redirect_regex(
                clean_path(first_response.redirect),
                first_path,
                clean_path(second_response.redirect),
                second_path,
            )

        self.content_parser = DynamicContentParser(first_response.content, second_response.content)

    def get_duplicate(self, response):
        for category in self.tested:
            for tester in self.tested[category].values():
                if response == tester.response:
                    return tester

        return None

    def is_wildcard(self, response):
        """Check if response is similar to wildcard response"""

        # Compare 2 binary responses (Response.content is empty if the body is binary)
        if not self.response.content and not response.content:
            return self.response.body == response.body

        return self.content_parser.compare_to(response.content)

    def check(self, path, response):
        """
        Perform analyzing to see if the response is wildcard or not
        """

        if self.response.status != response.status:
            return True

        # Read from line 129 to 138 to understand the workflow of this.
        if self.wildcard_redirect_regex and response.redirect:
            # - unquote(): Sometimes, some path characters get encoded or decoded in the response redirect
            # but it's still a wildcard redirect, so unquote everything to prevent false positives
            # - clean_path(): Get rid of queries and DOM in URL because of weird behaviours could happen
            # with them, so messy that I give up on finding a way to test them
            path = unquote(clean_path(path))
            redirect = unquote(clean_path(response.redirect))
            regex_to_compare = self.wildcard_redirect_regex.replace(
                REFLECTED_PATH_MARKER, re.escape(path)
            )
            is_wildcard_redirect = re.match(regex_to_compare, redirect, re.IGNORECASE)

            # If redirection doesn't match the rule, mark as found
            if not is_wildcard_redirect:
                return True

        if self.is_wildcard(response):
            return False

        return True

    @staticmethod
    def generate_redirect_regex(first_loc, first_path, second_loc, second_path):
        if first_path:
            first_loc = unquote(first_loc).replace(first_path, REFLECTED_PATH_MARKER)
        if second_path:
            second_loc = unquote(second_loc).replace(second_path, REFLECTED_PATH_MARKER)

        return generate_matching_regex(first_loc, second_loc)