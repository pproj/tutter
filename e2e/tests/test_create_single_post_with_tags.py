from lib.json_tree_validate import expect_json_tree, MagicExists, MagicAnyNumeric, MagicUnorderedList, MagicAnyOf
from lib import TestCaseBase


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
