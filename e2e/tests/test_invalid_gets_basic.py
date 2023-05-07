from lib import TestCaseBase
import random
import string


class InvalidGetsBasic(TestCaseBase):
    def run(self):
        # The db should be clean, so everything must return 404
        for res in ['author', 'post']:
            self.request_and_expect_status("GET", f"api/{res}/0", 404)
            self.request_and_expect_status("GET", f"api/{res}/1", 404)
            self.request_and_expect_status("GET", f"api/{res}/2", 404)
            self.request_and_expect_status("GET", f"api/{res}/100", 404)

        self.request_and_expect_status("GET", f"api/tag/asd", 404)
        self.request_and_expect_status("GET", f"api/tag/asdasd", 404)
        self.request_and_expect_status("GET", f"api/tag/asdasdasd", 404)
        self.request_and_expect_status("GET", f"api/tag/0", 404)

        # invalid datatypes
        for res in ['author', 'post']:
            self.request_and_expect_status("GET", f"api/{res}/a", 400)
            self.request_and_expect_status("GET", f"api/{res}/asd", 400)
            self.request_and_expect_status("GET", f"api/{res}/asdasd", 400)
            self.request_and_expect_status("GET", f"api/{res}/0xff", 400)
            self.request_and_expect_status("GET", f"api/{res}/b011", 400)
            self.request_and_expect_status("GET", f"api/{res}/10_10", 400)
            self.request_and_expect_status("GET", f"api/{res}/-10", 400)

        # no implicit octal parse test
        for i in range(10):
            post = {
                "author": str(i),
                "text": ''.join(random.choice(string.ascii_letters) for _ in range(160))
            }
            self.request_and_expect_status("POST", "/api/post", 201, json=post)

        self.request_and_expect_status("GET", f"api/author/10", 200)

        # dec 10 = oct 12
        self.request_and_expect_status("GET", f"api/author/012", 404)
