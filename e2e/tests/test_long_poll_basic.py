from lib import TestCaseBase
import threading
import requests
import time
from lib.json_tree_validate import expect_json_tree


class LongPollBasic(TestCaseBase):
    priority = -1

    def run(self):
        polled_r: requests.Response | None = None

        post = {
            "author": "alma",
            "text": "alma"
        }

        def long_wait():
            nonlocal polled_r
            polled_r = self.request_and_expect_status("GET", "/api/poll?last=0", 200)

        t = threading.Thread(target=long_wait)
        t.start()
        time.sleep(1)

        r = self.request_and_expect_status("POST", "/api/post", 201, json=post)
        post_1 = r.json()

        t.join()
        assert len(polled_r.json()) == 1
        expect_json_tree(post_1, polled_r.json()[0])

        r = self.request_and_expect_status("POST", "/api/post", 201, json=post)
        post_2 = r.json()

        r = self.request_and_expect_status("GET", "/api/poll?last=0", 200)
        assert len(r.json()) == 2
        expect_json_tree([post_1, post_2], r.json())

        r = self.request_and_expect_status("GET", "/api/poll?last=1", 200)
        assert len(r.json()) == 1
        expect_json_tree([post_2], r.json())

        got_exc = False
        try:
            self.request_and_expect_status("GET", "/api/poll?last=2", 200, timeout=5)
        except requests.exceptions.Timeout:
            got_exc = True

        assert got_exc
