import random
import string
from lib.json_tree_validate import expect_json_tree, MagicExists, MagicAnyNumeric
from lib import TestCaseBase


class CreateHugeAmountOfPosts(TestCaseBase):
    # This is kind of like stress-testing, but a lot lighter, only to test that the app wouldn't crash on light load
    # This test takes about 150sec on my machine

    priority = -2

    def run(self):
        expected_number = 5000  # takes about a minute on my machine
        for i in range(expected_number):
            post = {
                "author": ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(32)),
                "text": ''.join(random.choice(string.ascii_letters) for _ in range(160))
            }

            expected_author = {
                "id": MagicAnyNumeric(),
                "name": post['author'],
                "first_seen": MagicExists()
            }

            expected_post = {
                "id": i + 1,
                "created_at": MagicExists(),
                "text": post['text'],
                "author": expected_author,
                "tags": MagicExists()
            }

            r = self.request_and_expect_status("POST", "/api/post", 201, json=post)
            expect_json_tree(r.json(), expected_post)

        for i in range(expected_number):
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
            r = self.request_and_expect_status("GET", f"/api/post/{id_}", 200)
            expect_json_tree(r.json(), expected_post)

        for _ in range(500):
            r = self.request_and_expect_status("GET", f"/api/post", 200)
            assert len(r.json()) == expected_number, "Could not retrieve all posts created"
