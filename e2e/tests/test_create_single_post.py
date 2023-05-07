from lib.json_tree_validate import expect_json_tree, MagicExists
from lib import TestCaseBase


class CreateSinglePost(TestCaseBase):
    priority = 1

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
