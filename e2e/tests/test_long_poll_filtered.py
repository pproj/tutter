from lib import TestCaseBase
from lib.json_tree_validate import expect_json_tree
import threading
import requests
import time


class LongPollFiltered(TestCaseBase):
    priority = -1

    def run(self):
        polled_r_author: requests.Response | None = None
        polled_r_tag: requests.Response | None = None
        polled_exc_got_author: bool = False
        polled_exc_got_tag: bool = False

        post = {
            "author": "alma",
            "text": "alma #barack"
        }

        def long_wait_author_good():
            nonlocal polled_r_author
            polled_r_author = self.request_and_expect_status("GET", "/api/poll?last=0&author_id=1", 200, timeout=5)

        def long_wait_author_bad():
            nonlocal polled_exc_got_author
            try:
                self.request_and_expect_status("GET", "/api/poll?last=0&author_id=200", 200, timeout=5)
            except requests.Timeout:
                polled_exc_got_author = True

        def long_wait_tag_good():
            nonlocal polled_r_tag
            polled_r_tag = self.request_and_expect_status("GET", "/api/poll?last=0&tag=barack", 200, timeout=5)

        def long_wait_tag_bad():
            nonlocal polled_exc_got_tag
            try:
                self.request_and_expect_status("GET", "/api/poll?last=0&tag=asdasdasd", 200, timeout=5)
            except requests.Timeout:
                polled_exc_got_tag = True

        threads = []
        for func in [long_wait_author_good, long_wait_author_bad, long_wait_tag_good, long_wait_tag_bad]:
            t = threading.Thread(target=func)
            t.start()
            threads.append(t)

        time.sleep(1)

        r = self.request_and_expect_status("POST", "/api/post", 201, json=post)
        post_1 = r.json()

        for t in threads:
            t.join()

        assert len(polled_r_author.json()) == 1
        expect_json_tree(post_1, polled_r_author.json()[0])

        assert len(polled_r_tag.json()) == 1
        expect_json_tree(post_1, polled_r_tag.json()[0])

        assert polled_exc_got_author
        assert polled_exc_got_tag
