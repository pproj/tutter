from lib import TestCaseBase


class CheckOpenAPIAvailability(TestCaseBase):

    priority = 2

    def run(self):
        r = self.request_and_expect_status("GET", "/api/spec.yaml", 200)
        assert 'openapi' in r.text, "OpenAPI spec should contain the openapi word"

        r = self.request_and_expect_status("GET", "/api", 200)
        assert '</html>' in r.text, "Swagger UI missing html tag"
