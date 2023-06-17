from lib import TestCaseBase


class TestDebugInaccessible(TestCaseBase):

    priority = 2

    def run(self):
        # Debug pin is not set for the request_and_expect_status, so debug calls should fail
        self.request_and_expect_status("POST", "/api/debug/cleanup", 401)
        self.request_and_expect_status("PUT", "/api/debug/setTrending/asd", 401)
        self.request_and_expect_status("DELETE", "/api/debug/setTrending/asd", 401)
