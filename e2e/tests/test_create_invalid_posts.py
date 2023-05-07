from lib.json_tree_validate import expect_json_tree, MagicExists
from lib import TestCaseBase


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
                "text": "a" * 261
            },
            {
                "author": "alma",
                "text": "ű" * 261
            },
            {
                "author": "a" * 33,
                "text": "alma"
            },
            {
                "author": "<img />",
                "text": "<script></script>"
            },
            {
                "author": "asd",
                "text": "<script></script>"
            },
            {
                "author": "a a",
                "text": "alma"
            },
            {
                "author": "a a a a a a",
                "text": "alma"
            },
            {
                "author": "#asdasd",
                "text": "alma"
            },
            {
                "author": "@asdasd",
                "text": "alma"
            },
            {
                "author": "A_A",
                "text": "alma"
            },
            {
                "author": "eü",
                "text": "alma"
            },
            {
                "author": "'",
                "text": "alma"
            },
            {
                "author": "&nbsp;",
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
