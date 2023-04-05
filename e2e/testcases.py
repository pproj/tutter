import random
import string

from json_tree_validate import expect_json_tree, MagicExists, MagicAnyNumeric, MagicUnorderedList, MagicAnyOf
from testcase import TestCaseBase


class CheckOpenAPIAvailability(TestCaseBase):
    def run(self):
        r = self.request_and_expect_status("GET", "/api/spec.yaml", 200)
        assert 'openapi' in r.text, "OpenAPI spec should contain the openapi word"

        r = self.request_and_expect_status("GET", "/api", 200)
        assert '</html>' in r.text, "Swagger UI missing html tag"


class CreateSinglePost(TestCaseBase):
    def run(self):
        post = {
            "author": "alma",
            "text": "barack"
        }

        expected_author = {
            "id": 1,
            "name": post['author'],
            "first_seen": MagicExists()
        }

        expected_post = {
            "id": 1,
            "created_at": MagicExists(),
            "text": post['text'],
            "author": expected_author,
            "tags": []
        }

        r = self.request_and_expect_status("POST", "/api/post", 201, json=post)
        expect_json_tree(r.json(), expected_post)

        r = self.request_and_expect_status("GET", "/api/post", 200)
        expect_json_tree(r.json(), [expected_post])

        r = self.request_and_expect_status("GET", "/api/post/1", 200)
        expect_json_tree(r.json(), expected_post)

        r = self.request_and_expect_status("GET", "/api/author", 200)
        expect_json_tree(r.json(), [expected_author])

        del expected_post['author']
        expected_author["posts"] = [expected_post]

        r = self.request_and_expect_status("GET", "/api/author/1", 200)
        expect_json_tree(r.json(), expected_author)


class CreateSinglePostWithTags(TestCaseBase):
    def run(self):
        post = {
            "author": "alma",
            "text": "#barack #tutter #tutter #is #good"
        }
        tags_raw = ['barack', 'tutter', 'is', 'good']

        expected_author = {
            "id": 1,
            "name": post['author'],
            "first_seen": MagicExists()
        }

        expected_post = {
            "id": 1,
            "created_at": MagicExists(),
            "text": post['text'],
            "author": expected_author,
            "tags": MagicUnorderedList(tags_raw)
        }

        expected_tags = [
            {
                "tag": "barack",
                "first_seen": MagicExists()
            },
            {
                "tag": "tutter",
                "first_seen": MagicExists()
            },
            {
                "tag": "is",
                "first_seen": MagicExists()
            },
            {
                "tag": "good",
                "first_seen": MagicExists()
            }
        ]

        # the following block is just copied from CreateSinglePost
        r = self.request_and_expect_status("POST", "/api/post", 201, json=post)
        expect_json_tree(r.json(), expected_post)

        r = self.request_and_expect_status("GET", "/api/post", 200)
        expect_json_tree(r.json(), [expected_post])

        r = self.request_and_expect_status("GET", "/api/post/1", 200)
        expect_json_tree(r.json(), expected_post)

        r = self.request_and_expect_status("GET", "/api/author", 200)
        expect_json_tree(r.json(), [expected_author])

        for i, tag in enumerate(expected_tags):
            r = self.request_and_expect_status("GET", f"/api/tag/{tag['tag']}", 200)
            tag['posts'] = [expected_post]
            expect_json_tree(r.json(), expected_tags[i])

        unordered_expected_tags = [{"tag": MagicAnyOf(tags_raw), "first_seen": MagicExists()}] * len(tags_raw)
        r = self.request_and_expect_status("GET", "/api/tag", 200)
        expect_json_tree(r.json(), unordered_expected_tags)

        del expected_post['author']
        expected_author["posts"] = [expected_post]

        r = self.request_and_expect_status("GET", "/api/author/1", 200)
        expect_json_tree(r.json(), expected_author)


class CreateInvalidPosts(TestCaseBase):
    def run(self):
        invalid_posts = [
            {
                "author": "",
                "text": ""
            },
            {
                "author": "",
                "text": "alma"
            },
            {
                "author": "alma",
                "text": ""
            },
            {
                "author": "alma",
                "text": "a"*261
            },
            {
                "author": "a"*33,
                "text": "alma"
            },
        ]

        expected_result = {
            "reason": MagicExists()
        }

        for post in invalid_posts:
            r = self.request_and_expect_status("POST", "/api/post", 400, json=post)
            expect_json_tree(r.json(), expected_result)

        r = self.request_and_expect_status("GET", "/api/post", 200)
        assert len(r.json()) == 0


class CreatePostWithInvalidTags(TestCaseBase):
    def run(self):
        cases = [
            ("@#", []),
            ("#@ #- #= #/", []),
            ("# # # #", []),
            ("####asd", ['asd']),
            ("#" * 260, []),
            ("#asdÁÁÁÁ", ['asd']),
            ("#tutter #tutter #tutter #tutter", ['tutter']),
            ("#tutter #TuTteR #TUTTER #tuTter #tUtteR", ['tutter']),
        ]

        for message, expected_tags in cases:
            post = {
                "author": "alma",
                "text": message
            }

            expected_author = {
                "id": 1,
                "name": post['author'],
                "first_seen": MagicExists()
            }

            expected_post = {
                "id": MagicAnyNumeric(),
                "created_at": MagicExists(),
                "text": post['text'],
                "author": expected_author,
                "tags": MagicUnorderedList(expected_tags)
            }

            r = self.request_and_expect_status("POST", "/api/post", 201, json=post)
            expect_json_tree(r.json(), expected_post)


class CreateHugeAmountOfPosts(TestCaseBase):
    # This is kind of like stress-testing, but a lot lighter, only to test that the app wouldn't crash on light load
    # This test takes about 150sec on my machine
    def run(self):
        expected_number = 5000  # takes about a minute on my machine
        for i in range(expected_number):
            post = {
                "author": ''.join(random.choice(string.ascii_letters) for i in range(32)),
                "text": ''.join(random.choice(string.ascii_letters) for i in range(160))
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
