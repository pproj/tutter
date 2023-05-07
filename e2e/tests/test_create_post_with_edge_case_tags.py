from lib.json_tree_validate import expect_json_tree, MagicExists, MagicAnyNumeric, MagicUnorderedList, MagicAnyOf
from lib import TestCaseBase


class CreatePostWithEdgeCaseTags(TestCaseBase):
    def run(self):
        cases = [
            ("@#", []),
            ("#@ #- #= #/", []),
            ("# # # #", []),
            ("####asd", ['asd']),
            ("#" * 260, []),
            ("#asdÁÁÁÁ", ['asd']),
            ("#asd123", ['asd123']),
            ("#1 #2 #3", ['1', '2', '3']),
            ("#tutter #tutter #tutter #tutter", ['tutter']),
            ("#tutter #TuTteR #TUTTER #tuTter #tUtteR", ['tutter']),
            (
                "#a #b #c #d #e #f #g #h #i #j #k #l #m #n #o #p #q #r #s #t #u #v #w #x #y #z #0 #1 #2 #3 #4 #5 #6 #7 #8 #9 #a #b #c #d #e #f #g #h #i #j #k #l #m #n #o #p #q #r #s #t #u #v #w #x #y #z #0 #1 #2 #3 #4 #5 #6 #7 #8 #9 #a #b #c #d #e #f #g #h #i #j #k #l #m #n #o",
                ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
                 'u', 'v', 'w', 'x', 'y', 'z', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
            ),
            ("#a " * int(260 / 3), ['a']),
            ("#a ", ['a']),
            (" #a", ['a']),
            (" #a ", ['a']),
            ("   #a   ", ['a']),
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
                "text": post['text'].strip(),
                "author": expected_author,
                "tags": MagicUnorderedList(expected_tags)
            }

            r = self.request_and_expect_status("POST", "/api/post", 201, json=post)
            expect_json_tree(r.json(), expected_post)
