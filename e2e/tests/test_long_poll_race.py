from lib import TestCaseBase
import threading
import random
import requests
import time


class LongPollRace(TestCaseBase):
    priority = -1

    class LPReader(threading.Thread):
        def __init__(self, testcase):
            super().__init__()
            self.responses = set()
            self.errors = []
            self.running = True
            self.testcase: TestCaseBase = testcase
            self._remaining_passes = 2
            self._last = 0

        def loop(self):
            timeout = random.random() * 5
            try:
                r = self.testcase.session.get("/api/poll?last=" + str(self._last), timeout=timeout)
            except requests.exceptions.Timeout:
                return  # new loop

            if r.status_code == 204:
                return  # new loop

            elif r.status_code == 200:
                last_before = self._last
                assert len(r.json()) > 0
                for post in r.json():
                    post_id = post['id']
                    assert post_id > last_before
                    self.responses.add(post_id)
                    if post_id > self._last:
                        self._last = post_id
                assert self._last > last_before

            else:
                raise Exception("Unexpected HTTP response: " + r.status_code)

        def run(self):
            while self._remaining_passes > 0:
                if not self.running:
                    self._remaining_passes -= 1
                if random.random() > 0.5:
                    time.sleep(random.random() * 0.01)

                try:
                    self.loop()
                except Exception as e:
                    self.errors.append(e)

    def run(self):
        post = {
            "author": "alma",
            "text": "alma"
        }
        NUM_POLLERS = 100
        NUM_POSTS = 2500

        pollers = []
        for i in range(NUM_POLLERS):
            time.sleep(0.001)
            p = self.LPReader(self)
            pollers.append(p)
            p.start()

        try:
            for i in range(NUM_POSTS):
                if random.random() > 0.5:
                    time.sleep(random.random() * 0.001)
                self.request_and_expect_status("POST", "/api/post", 201, json=post)

        finally:
            for p in pollers:
                p.running = False

            for p in pollers:
                p.join()

            for p in pollers:
                assert len(p.responses) == NUM_POSTS
                assert len(p.errors) == 0
