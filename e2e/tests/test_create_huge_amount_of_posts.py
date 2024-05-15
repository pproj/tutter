import random
import string
from lib.json_tree_validate import expect_json_tree, MagicExists, MagicAnyNumeric
from lib import TestCaseBase
import threading


class CreateHugeAmountOfPosts(TestCaseBase):
    # This test is actually adjusted for a real word test... we originally ran this test with 5000 posts, that was successfully
    # But on the actual event in 2023 the system crashed when the number of posts went above a few millions.
    # The reason behind this was gorm's stupid join method

    priority = -2

    class CreatorThread(threading.Thread):
        def __init__(self, testcase, id, amount:int):
            super().__init__()
            self._amount = amount
            self._id = id

            self.testcase: TestCaseBase = testcase

            self.exc = None

        def _protected_run(self):
            for i in range(self._amount):
                unique_author_name = str(self._id) + "_" + str(i) + "_" + ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(15))

                post = {
                    "author": unique_author_name,
                    "text": ''.join(random.choice(string.ascii_letters) for _ in range(160))
                }

                expected_author = {
                    "id": MagicAnyNumeric(),
                    "name": post['author'],
                    "first_seen": MagicExists()
                }

                expected_post = {
                    "id": MagicAnyNumeric(),  # we can no longer verify it because we are running multi-threaded
                    "created_at": MagicExists(),
                    "text": post['text'],
                    "author": expected_author,
                    "tags": MagicExists()
                }

                r = self.testcase.request_and_expect_status("POST", "/api/post", 201, json=post)
                expect_json_tree(r.json(), expected_post)

        def run(self):
            try:
                self._protected_run()
            except Exception as e:
                self.exc = e

    class VerifierThread(threading.Thread):
        def __init__(self, testcase, id, start:int, end:int):
            super().__init__()
            self._start = start # incl
            self._end = end # excl
            self._id = id

            self.testcase: TestCaseBase = testcase

            self.exc = None

        def _protected_run(self):
            for i in range(self._start, self._end):
                id_ = i + 1
                expected_post = {
                    "id": id_,
                    "created_at": MagicExists(),
                    "text": MagicExists(),
                    "author": {
                        "id": MagicAnyNumeric(),
                        "name": MagicExists(),
                        "first_seen": MagicExists()
                    },
                    "tags": MagicExists()
                }
                r = self.testcase.request_and_expect_status("GET", f"/api/post/{id_}", 200)
                expect_json_tree(r.json(), expected_post)

        def run(self):
            try:
                self._protected_run()
            except Exception as e:
                self.exc = e


    def run(self):
        expected_number = 65536 + 64 # should break stuff
        thread_count = 16
        chunk_size = int(expected_number / thread_count)

        assert chunk_size*thread_count == expected_number

        threads = []
        for i in range(thread_count):
            t = CreateHugeAmountOfPosts.CreatorThread(self, i, chunk_size)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()
            if t.exc:
                raise t.exc

        threads = []
        for i in range(thread_count):
            t = CreateHugeAmountOfPosts.VerifierThread(self, i, i*chunk_size, (i+1)*chunk_size)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()
            if t.exc:
                raise t.exc


        for _ in range(5):
            r = self.request_and_expect_status("GET", f"/api/post", 200)
            assert len(r.json()) == expected_number, "Could not retrieve all posts created"
