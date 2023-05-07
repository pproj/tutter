from lib.json_tree_validate import expect_json_tree, MagicExists, MagicAnyNumeric, MagicUnorderedList
from lib import TestCaseBase


class CreateEdgeCasePosts(TestCaseBase):
    def run(self):
        cases = [
            (
                "'"*260,
                "'" * 260,
                []
            ),
            (
                "<asd>hello</asd>",
                "hello",
                []
            ),
            (
                "<asd href=' #tutter '>hello</asd>",
                "hello",
                []
            ),
            (
                "<- arra van buda",
                "<- arra van buda",
                []
            ),
            (
                "<- mindkettő irányban van valami ->",
                "<- mindkettő irányban van valami ->",
                []
            ),
            (
                "#< asd",
                "#< asd",
                []
            ),
            (
                "#<",
                "#<",
                []
            ),
            (
                "<#>",
                "<#>",
                []
            ),
            (
                "<#tutter>",
                "<#tutter>",
                ['tutter']
            ),
        ]

        for message, expected_message, expected_tags in cases:
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
                "text": expected_message,
                "author": expected_author,
                "tags": MagicUnorderedList(expected_tags)
            }

            r = self.request_and_expect_status("POST", "/api/post", 201, json=post)
            expect_json_tree(r.json(), expected_post)
