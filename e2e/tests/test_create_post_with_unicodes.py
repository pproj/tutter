from lib.json_tree_validate import expect_json_tree, MagicExists, MagicAnyNumeric
from lib import TestCaseBase


class CreatePostWithUnicodes(TestCaseBase):
    def run(self):
        cases = [
            "á" * 260,
            "ü" * 260,
            "ű" * 260,
            "Á" * 260,
            "ó" * 260,
            "😀" * 260,
            "😎" * 260,
            "👌" * 260,
            "a" * 259 + "á",
            "a" * 259 + "👌",
        ]

        for message in cases:
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
                "text": post['text'].strip(),
                "author": expected_author,
                "tags": []
            }

            r = self.request_and_expect_status("POST", "/api/post", 201, json=post)
            expect_json_tree(r.json(), expected_post)
