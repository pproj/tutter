import random
import string
import threading
import time
from datetime import datetime

import requests.exceptions

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
            {  # this is refused because it would evaluate to empty posts
                "author": "<img />",
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
        ]

        expected_result = {
            "reason": MagicExists()
        }

        for post in invalid_posts:
            r = self.request_and_expect_status("POST", "/api/post", 400, json=post)
            expect_json_tree(r.json(), expected_result)

        r = self.request_and_expect_status("GET", "/api/post", 200)
        assert len(r.json()) == 0


class CreatePostWithUnicodes(TestCaseBase):
    def run(self):
        cases = [
            "á"*260,
            "ü"*260,
            "ű"*260,
            "Á"*260,
            "ó"*260,
            "😀"*260,
            "😎"*260,
            "👌"*260,
            "a"*259 + "á",
            "a"*259 + "👌",
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


class InvalidGetsBasic(TestCaseBase):
    def run(self):
        # The db should be clean, so everything must return 404
        for res in ['author', 'post']:
            self.request_and_expect_status("GET", f"api/{res}/0", 404)
            self.request_and_expect_status("GET", f"api/{res}/1", 404)
            self.request_and_expect_status("GET", f"api/{res}/2", 404)
            self.request_and_expect_status("GET", f"api/{res}/100", 404)

        self.request_and_expect_status("GET", f"api/tag/asd", 404)
        self.request_and_expect_status("GET", f"api/tag/asdasd", 404)
        self.request_and_expect_status("GET", f"api/tag/asdasdasd", 404)
        self.request_and_expect_status("GET", f"api/tag/0", 404)

        # invalid datatypes
        for res in ['author', 'post']:
            self.request_and_expect_status("GET", f"api/{res}/a", 400)
            self.request_and_expect_status("GET", f"api/{res}/asd", 400)
            self.request_and_expect_status("GET", f"api/{res}/asdasd", 400)
            self.request_and_expect_status("GET", f"api/{res}/0xff", 400)
            self.request_and_expect_status("GET", f"api/{res}/b011", 400)
            self.request_and_expect_status("GET", f"api/{res}/10_10", 400)
            self.request_and_expect_status("GET", f"api/{res}/-10", 400)

        # no implicit octal parse test
        for i in range(10):
            post = {
                "author": str(i),
                "text": ''.join(random.choice(string.ascii_letters) for _ in range(160))
            }
            self.request_and_expect_status("POST", "/api/post", 201, json=post)

        self.request_and_expect_status("GET", f"api/author/10", 200)

        # dec 10 = oct 12
        self.request_and_expect_status("GET", f"api/author/012", 404)


class CreateHugeAmountOfPosts(TestCaseBase):
    # This is kind of like stress-testing, but a lot lighter, only to test that the app wouldn't crash on light load
    # This test takes about 150sec on my machine
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


class InvalidFilters(TestCaseBase):
    def run(self):
        # commons
        for res in ["post", "author", "tag"]:
            self.request_and_expect_status("GET", f"/api/{res}?limit=0", 400)
            self.request_and_expect_status("GET", f"/api/{res}?limit=-2", 400)
            self.request_and_expect_status("GET", f"/api/{res}?order=asd", 400)
            self.request_and_expect_status("GET", f"/api/{res}?order=asd&limit=0", 400)

        # associated
        for res in ["author", "tag"]:
            # 1 can both be id and tag
            self.request_and_expect_status("GET", f"/api/{res}/1?fill=asd", 400)
            self.request_and_expect_status("GET", f"/api/{res}/1?fill=-12", 400)
            self.request_and_expect_status("GET", f"/api/{res}/1?fill=false&limit=1", 400)
            self.request_and_expect_status("GET", f"/api/{res}/1?fill=false&order=asc", 400)
            self.request_and_expect_status("GET", f"/api/{res}/1?fill=false&offset=2", 400)

        # post only

        # before and before_id must not be used together
        self.request_and_expect_status("GET", f"/api/post?before=2023-03-28T01:01:10%2b02:00&before_id=12", 400)

        # after and after_id must not be used together
        self.request_and_expect_status("GET", f"/api/post?after=2023-03-28T01:01:10%2b02:00&after_id=12", 400)

        # before must be after after
        self.request_and_expect_status("GET",
                                       f"/api/post?after=2023-03-29T01:01:10%2b02:00&before=2023-03-28T01:01:10%2b02:00",
                                       400)
        self.request_and_expect_status("GET",
                                       f"/api/post?after=2023-03-28T01:01:10%2b02:00&before=2023-03-28T01:01:10%2b02:00",
                                       400)
        self.request_and_expect_status("GET", f"/api/post?after_id=12&before_id=9", 400)
        self.request_and_expect_status("GET", f"/api/post?after_id=9&before_id=9", 400)

        # tag can not be empty string
        self.request_and_expect_status("GET", f"/api/post?tag=", 400)
        self.request_and_expect_status("GET", f"/api/post?tag=&tag=&tag=", 400)


class PostFiltersByAssociation(TestCaseBase):
    def run(self):
        # Create some test posts

        authors = ['a', 'b']
        tags = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
        total_posts = 0
        posts_by_authors = {}.fromkeys(authors, 0)
        posts_by_tags = {}.fromkeys(tags, 0)

        for author in authors:
            for i in range(len(tags) - 2):
                total_posts += 1
                posts_by_authors[author] += 1
                posts_by_tags[tags[i]] += 1
                posts_by_tags[tags[i + 1]] += 1
                posts_by_tags[tags[i + 2]] += 1
                post = {
                    "author": author,
                    "text": f"#{tags[i]} #{tags[i + 1]} #{tags[i + 2]}"
                }
                self.request_and_expect_status("POST", "/api/post", 201, json=post)

        r = self.request_and_expect_status("GET", "/api/post", 200)
        assert len(r.json()) == total_posts

        r = self.request_and_expect_status("GET", "/api/author", 200)
        assert len(r.json()) == len(authors)

        r = self.request_and_expect_status("GET", "/api/tag", 200)
        assert len(r.json()) == len(tags)

        # run queries for author
        for i, author in enumerate(authors):
            r = self.request_and_expect_status("GET", f"/api/post?author_id={i + 1}", 200)
            assert len(r.json()) == posts_by_authors[author]
            for post in r.json():
                assert post["author"]["id"] == i + 1
                assert post["author"]["name"] == author

        # run queries for author
        for i, author1 in enumerate(authors):
            for j, author2 in enumerate(authors):
                r = self.request_and_expect_status("GET", f"/api/post?author_id={i + 1}&author_id={j + 1}", 200)

                if i == j:
                    assert len(r.json()) == posts_by_authors[author1]
                    for post in r.json():
                        assert post["author"]["id"] == i + 1
                        assert post["author"]["name"] == author1
                else:
                    assert len(r.json()) == posts_by_authors[author1] + posts_by_authors[author2]
                    for post in r.json():
                        assert post["author"]["id"] in [i + 1, j + 1]
                        assert post["author"]["name"] in [author1, author2]

        # run queries for tags (should be rewritten for generics)
        for tag in tags:
            r = self.request_and_expect_status("GET", "/api/post?tag=" + tag, 200)
            assert len(r.json()) == posts_by_tags[tag]
            for post in r.json():
                assert tag in post["tags"]

        for tag1 in tags:
            for tag2 in tags:
                r = self.request_and_expect_status("GET", f"/api/post?tag={tag1}&={tag2}", 200)
                for post in r.json():
                    assert (tag1 in post["tags"]) or (tag2 in post["tags"])

        for tag1 in tags:
            for tag2 in tags:
                for tag3 in tags:
                    r = self.request_and_expect_status("GET", f"/api/post?tag={tag1}&={tag2}&tag={tag3}", 200)
                    for post in r.json():
                        assert (tag1 in post["tags"]) or (tag2 in post["tags"]) or (tag3 in post["tags"])

        # existing and non-existing mixed
        for tag1 in tags:
            for tag2 in tags:
                r = self.request_and_expect_status("GET", f"/api/post?tag={tag1}&={tag2}&tag=asd&tag=www", 200)
                for post in r.json():
                    assert (tag1 in post["tags"]) or (tag2 in post["tags"])

        # non-existing things
        r = self.request_and_expect_status("GET", f"/api/post?tag=lll", 200)
        assert len(r.json()) == 0

        r = self.request_and_expect_status("GET", f"/api/post?tag=lll&=aaa&tag=asd&tag=www", 200)
        assert len(r.json()) == 0

        r = self.request_and_expect_status("GET", f"/api/post?author_id=9999", 200)
        assert len(r.json()) == 0

        r = self.request_and_expect_status("GET", f"/api/post?author_id=9999&author_id=9998&author_id=9997", 200)
        assert len(r.json()) == 0


class OtherPostFilters(TestCaseBase):
    def run(self):
        # Create some test posts

        authors = ['a', 'b']
        tags = ['a', 'b', 'c', 'd', 'e', 'f']
        total_posts = 0
        post_times = []

        for author in authors:
            for i in range(len(tags) - 2):
                total_posts += 1
                post = {
                    "author": author,
                    "text": f"#{tags[i]} #{tags[i + 1]} #{tags[i + 2]}"
                }
                r = self.request_and_expect_status("POST", "/api/post", 201, json=post)
                post_times.append(r.json()['created_at'])
                time.sleep(0.2)  # make after and before easier

        r = self.request_and_expect_status("GET", "/api/post", 200)
        assert len(r.json()) == total_posts

        r = self.request_and_expect_status("GET", "/api/author", 200)
        assert len(r.json()) == len(authors)

        r = self.request_and_expect_status("GET", "/api/tag", 200)
        assert len(r.json()) == len(tags)

        # And now something completely different

        # # # ID based # # #

        # after_id only
        for i in range(total_posts + 5):
            after_id = i + 1

            r = self.request_and_expect_status("GET", f"/api/post?after_id={after_id}", 200)

            assert len(r.json()) == max(total_posts - after_id, 0)

            for post in r.json():
                assert post['id'] > after_id

        # before_id only
        for i in range(total_posts + 5):
            before_id = i + 1

            r = self.request_and_expect_status("GET", f"/api/post?before_id={before_id}", 200)

            assert len(r.json()) == min(i, total_posts)

            for post in r.json():
                assert post['id'] < before_id

        # after_id + before_id
        for i in range(total_posts):
            for j in range(total_posts):
                before_id = i + 1
                after_id = j + 1
                if after_id < before_id:
                    expected_status = 200
                else:
                    expected_status = 400

                r = self.request_and_expect_status("GET", f"/api/post?before_id={before_id}&after_id={after_id}",
                                                   expected_status)

                if expected_status != 200:
                    continue

                # followings are for 200 only
                assert len(r.json()) == max(before_id - after_id - 1, 0)

                for post in r.json():
                    assert post['id'] > after_id
                    assert post['id'] < before_id

        # # # TS based # # #

        # after only
        for i, ts in enumerate(post_times):

            r = self.request_and_expect_status("GET", f"/api/post?after={ts.replace('+', '%2b')}", 200)

            assert len(r.json()) == max(total_posts - i - 1, 0)

            for post in r.json():
                created_at = datetime.fromisoformat(post['created_at'])
                ts_dt = datetime.fromisoformat(ts)
                assert created_at > ts_dt

        # before only
        for i, ts in enumerate(post_times):

            r = self.request_and_expect_status("GET", f"/api/post?before={ts.replace('+', '%2b')}", 200)

            assert len(r.json()) == min(i, total_posts)

            for post in r.json():
                created_at = datetime.fromisoformat(post['created_at'])
                ts_dt = datetime.fromisoformat(ts)
                assert created_at < ts_dt

        # after + before
        for i, before_str in enumerate(post_times):
            for j, after_str in enumerate(post_times):
                after_dt = datetime.fromisoformat(after_str)
                before_dt = datetime.fromisoformat(before_str)

                if after_dt < before_dt:
                    expected_status = 200
                else:
                    expected_status = 400

                r = self.request_and_expect_status(
                    "GET",
                    f"/api/post?before={before_str.replace('+', '%2b')}&after={after_str.replace('+', '%2b')}",
                    expected_status
                )

                if expected_status != 200:
                    continue

                # followings are for 200 only
                assert len(r.json()) == max(i - j - 1, 0)

                for post in r.json():
                    created_at = datetime.fromisoformat(post['created_at'])
                    assert created_at > after_dt
                    assert created_at < before_dt

        # # # Mixed # # #

        # after_id + before
        for i in range(total_posts):
            for after_str in post_times:
                before_id = i + 1
                after_dt = datetime.fromisoformat(after_str)

                r = self.request_and_expect_status(
                    "GET",
                    f"/api/post?before_id={before_id}&after={after_str.replace('+', '%2b')}",
                    200
                )

                for post in r.json():
                    created_at = datetime.fromisoformat(post['created_at'])
                    assert created_at > after_dt
                    assert post['id'] < before_id

        # after + before_id
        for i in range(total_posts):
            for before_str in post_times:
                after_id = i + 1
                before_dt = datetime.fromisoformat(before_str)

                r = self.request_and_expect_status(
                    "GET",
                    f"/api/post?before={before_str.replace('+', '%2b')}&after_id={after_id}",
                    200
                )

                for post in r.json():
                    created_at = datetime.fromisoformat(post['created_at'])
                    assert created_at < before_dt
                    assert post['id'] > after_id


class FiltersTopLevelBasic(TestCaseBase):

    def do_magic(self, resource: str, count: int):
        # simple ordering
        r = self.request_and_expect_status("GET", f"/api/{resource}?order=asc", 200)
        last_id = 0
        for post in r.json():
            assert post['id'] > last_id
            last_id = post['id']

        r = self.request_and_expect_status("GET", f"/api/{resource}?order=desc", 200)
        last_id = 999
        for post in r.json():
            assert post['id'] < last_id
            last_id = post['id']

        # limit checks
        for i in range(count + 10):
            r = self.request_and_expect_status("GET", f"/api/{resource}?limit={i + 1}", 200)
            assert len(r.json()) == min(i + 1, count)

        # limit + ordering
        for i in range(count + 10):
            r = self.request_and_expect_status("GET", f"/api/{resource}?limit={i + 1}&order=asc", 200)
            assert len(r.json()) == min(i + 1, count)
            last_id = 0
            for post in r.json():
                assert post['id'] > last_id
                last_id = post['id']

        for i in range(count + 10):
            r = self.request_and_expect_status("GET", f"/api/{resource}?limit={i + 1}&order=desc", 200)
            assert len(r.json()) == min(i + 1, count)
            last_id = 999
            for post in r.json():
                assert post['id'] < last_id
                last_id = post['id']

        # offset
        for i in range(count + 10):
            r = self.request_and_expect_status("GET", f"/api/{resource}?offset={i}", 200)
            assert len(r.json()) == max(0, count - i)

        # offset + ordering
        for i in range(count + 10):
            r = self.request_and_expect_status("GET", f"/api/{resource}?offset={i}&order=asc", 200)
            next_id = i + 1
            for post in r.json():
                assert post['id'] == next_id
                next_id += 1

            assert len(r.json()) == max(0, count - i)

        for i in range(count + 10):
            r = self.request_and_expect_status("GET", f"/api/{resource}?offset={i}&order=desc", 200)
            next_id = count - i
            for post in r.json():
                assert post['id'] == next_id
                next_id -= 1

            assert len(r.json()) == max(0, count - i)

        # limit + offset
        for i in range(count + 10):  # offset
            for j in range(count + 10):  # limit
                r = self.request_and_expect_status("GET", f"/api/{resource}?offset={i}&limit={j + 1}", 200)

                desired_len = min(min(j + 1, count), count - i)
                if i > count:
                    desired_len -= (count - i)

                assert len(r.json()) == desired_len

        # limit + offset + ordering
        for i in range(count + 10):  # offset
            for j in range(count + 10):  # limit
                r = self.request_and_expect_status("GET", f"/api/{resource}?offset={i}&limit={j + 1}&order=asc", 200)

                desired_len = min(min(j + 1, count), count - i)
                if i > count:
                    desired_len -= (count - i)

                assert len(r.json()) == desired_len

                next_id = i + 1
                for post in r.json():
                    assert post['id'] == next_id
                    next_id += 1

        for i in range(count + 10):  # offset
            for j in range(count + 10):  # limit
                r = self.request_and_expect_status("GET", f"/api/{resource}?offset={i}&limit={j + 1}&order=desc", 200)

                desired_len = min(min(j + 1, count), count - i)
                if i > count:
                    desired_len -= (count - i)

                assert len(r.json()) == desired_len

                next_id = count - i
                for post in r.json():
                    assert post['id'] == next_id
                    next_id -= 1

    def do_tags_magic(self, count):
        resource = "tag"

        # WARNING: first_seen is not the order base on the server side, but it should reflect what we want pretty well

        # simple ordering
        r = self.request_and_expect_status("GET", f"/api/{resource}?order=asc", 200)
        if len(r.json()) > 1:
            last_first_seen = datetime.fromisoformat(r.json()[0]['first_seen'])
            for post in r.json()[1:]:
                first_seen = datetime.fromisoformat(post['first_seen'])
                assert first_seen >= last_first_seen
                last_first_seen = first_seen

        r = self.request_and_expect_status("GET", f"/api/{resource}?order=desc", 200)
        if len(r.json()) > 1:
            last_first_seen = datetime.fromisoformat(r.json()[0]['first_seen'])
            for post in r.json()[1:]:
                first_seen = datetime.fromisoformat(post['first_seen'])
                assert first_seen <= last_first_seen
                last_first_seen = first_seen

        # limit checks
        for i in range(count + 10):
            r = self.request_and_expect_status("GET", f"/api/{resource}?limit={i + 1}", 200)
            assert len(r.json()) == min(i + 1, count)

        # limit + ordering
        for i in range(count + 10):
            r = self.request_and_expect_status("GET", f"/api/{resource}?limit={i + 1}&order=asc", 200)
            assert len(r.json()) == min(i + 1, count)
            if len(r.json()) > 1:
                last_first_seen = datetime.fromisoformat(r.json()[0]['first_seen'])
                for post in r.json()[1:]:
                    first_seen = datetime.fromisoformat(post['first_seen'])
                    assert first_seen >= last_first_seen
                    last_first_seen = first_seen

        for i in range(count + 10):
            r = self.request_and_expect_status("GET", f"/api/{resource}?limit={i + 1}&order=desc", 200)
            assert len(r.json()) == min(i + 1, count)
            if len(r.json()) > 1:
                last_first_seen = datetime.fromisoformat(r.json()[0]['first_seen'])
                for post in r.json()[1:]:
                    first_seen = datetime.fromisoformat(post['first_seen'])
                    assert first_seen <= last_first_seen
                    last_first_seen = first_seen

        # offset
        for i in range(count + 10):
            r = self.request_and_expect_status("GET", f"/api/{resource}?offset={i}", 200)
            assert len(r.json()) == max(0, count - i)

        # offset + ordering
        for i in range(count + 10):
            r = self.request_and_expect_status("GET", f"/api/{resource}?offset={i}&order=asc", 200)
            if len(r.json()) > 1:
                last_first_seen = datetime.fromisoformat(r.json()[0]['first_seen'])
                for post in r.json()[1:]:
                    first_seen = datetime.fromisoformat(post['first_seen'])
                    assert first_seen >= last_first_seen
                    last_first_seen = first_seen

            assert len(r.json()) == max(0, count - i)

        for i in range(count + 10):
            r = self.request_and_expect_status("GET", f"/api/{resource}?offset={i}&order=desc", 200)
            if len(r.json()) > 1:
                last_first_seen = datetime.fromisoformat(r.json()[0]['first_seen'])
                for post in r.json()[1:]:
                    first_seen = datetime.fromisoformat(post['first_seen'])
                    assert first_seen <= last_first_seen
                    last_first_seen = first_seen

            assert len(r.json()) == max(0, count - i)

        # limit + offset
        for i in range(count + 10):  # offset
            for j in range(count + 10):  # limit
                r = self.request_and_expect_status("GET", f"/api/{resource}?offset={i}&limit={j + 1}", 200)

                desired_len = min(min(j + 1, count), count - i)
                if i > count:
                    desired_len -= (count - i)

                assert len(r.json()) == desired_len

        # limit + offset + ordering
        for i in range(count + 10):  # offset
            for j in range(count + 10):  # limit
                r = self.request_and_expect_status("GET", f"/api/{resource}?offset={i}&limit={j + 1}&order=asc", 200)

                desired_len = min(min(j + 1, count), count - i)
                if i > count:
                    desired_len -= (count - i)

                assert len(r.json()) == desired_len

                if len(r.json()) > 1:
                    last_first_seen = datetime.fromisoformat(r.json()[0]['first_seen'])
                    for post in r.json()[1:]:
                        first_seen = datetime.fromisoformat(post['first_seen'])
                        assert first_seen >= last_first_seen
                        last_first_seen = first_seen

        for i in range(count + 10):  # offset
            for j in range(count + 10):  # limit
                r = self.request_and_expect_status("GET", f"/api/{resource}?offset={i}&limit={j + 1}&order=desc", 200)

                desired_len = min(min(j + 1, count), count - i)
                if i > count:
                    desired_len -= (count - i)

                assert len(r.json()) == desired_len

                if len(r.json()) > 1:
                    last_first_seen = datetime.fromisoformat(r.json()[0]['first_seen'])
                    for post in r.json()[1:]:
                        first_seen = datetime.fromisoformat(post['first_seen'])
                        assert first_seen <= last_first_seen
                        last_first_seen = first_seen

    def run(self):
        authors = ['a', 'b', 'c']
        tags = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
        total_posts = 0
        times = []

        for author in authors:
            for i in range(len(tags) - 2):
                total_posts += 1
                post = {
                    "author": author,
                    "text": f"alma #{tags[i]} #{tags[i + 1]} #{tags[i + 2]}"
                }
                r = self.request_and_expect_status("POST", "/api/post", 201, json=post)
                times.append(r.json()['created_at'])

        r = self.request_and_expect_status("GET", "/api/post", 200)
        assert len(r.json()) == total_posts

        r = self.request_and_expect_status("GET", "/api/author", 200)
        assert len(r.json()) == len(authors)

        r = self.request_and_expect_status("GET", "/api/tag", 200)
        assert len(r.json()) == len(tags)

        # and now, run some queries
        self.do_magic("post", total_posts)
        self.do_magic("author", len(authors))
        self.do_tags_magic(len(tags))


class FiltersRelatedBasic(TestCaseBase):

    @staticmethod
    def assert_asc(l: list, key):
        if len(l) > 0:
            if key:
                last_id = l[0][key]
            else:
                last_id = l[0]
            last_id -= 1
            for p in l:
                if key:
                    assert p[key] > last_id
                    last_id = p[key]
                else:
                    assert p > last_id
                    last_id = p

    @staticmethod
    def assert_desc(l: list, key):
        if len(l) > 0:
            if key:
                last_id = l[0][key]
            else:
                last_id = l[0]
            last_id += 1
            for p in l:
                if key:
                    assert p[key] < last_id
                    last_id = p[key]
                else:
                    assert p < last_id
                    last_id = p

    def do_magic(self, resource_type: str, resource_id: str, count: int):
        # simple ordering
        r = self.request_and_expect_status("GET", f"/api/{resource_type}/{resource_id}?order=asc", 200)
        self.assert_asc(r.json()['posts'], 'id')

        r = self.request_and_expect_status("GET", f"/api/{resource_type}/{resource_id}?order=desc", 200)
        self.assert_desc(r.json()['posts'], 'id')

        # limit checks
        for i in range(count + 10):
            r = self.request_and_expect_status("GET", f"/api/{resource_type}/{resource_id}?limit={i + 1}", 200)
            assert len(r.json()['posts']) == min(i + 1, count)

        # limit + ordering
        for i in range(count + 10):
            r = self.request_and_expect_status("GET", f"/api/{resource_type}/{resource_id}?limit={i + 1}&order=asc",
                                               200)
            assert len(r.json()['posts']) == min(i + 1, count)
            self.assert_asc(r.json()['posts'], 'id')

        for i in range(count + 10):
            r = self.request_and_expect_status("GET", f"/api/{resource_type}/{resource_id}?limit={i + 1}&order=desc",
                                               200)
            assert len(r.json()['posts']) == min(i + 1, count)
            self.assert_desc(r.json()['posts'], 'id')

        # offset
        for i in range(count + 10):
            r = self.request_and_expect_status("GET", f"/api/{resource_type}/{resource_id}?offset={i}", 200)
            assert len(r.json()['posts']) == max(0, count - i)

        # offset + ordering
        for i in range(count + 10):
            r = self.request_and_expect_status("GET", f"/api/{resource_type}/{resource_id}?offset={i}&order=asc", 200)
            assert len(r.json()['posts']) == max(0, count - i)
            self.assert_asc(r.json()['posts'], 'id')

        for i in range(count + 10):
            r = self.request_and_expect_status("GET", f"/api/{resource_type}/{resource_id}?offset={i}&order=desc", 200)
            assert len(r.json()['posts']) == max(0, count - i)
            self.assert_desc(r.json()['posts'], 'id')

        # limit + offset
        for i in range(count + 10):  # offset
            for j in range(count + 10):  # limit
                r = self.request_and_expect_status("GET",
                                                   f"/api/{resource_type}/{resource_id}?offset={i}&limit={j + 1}", 200)

                desired_len = min(min(j + 1, count), count - i)
                if i > count:
                    desired_len -= (count - i)

                assert len(r.json()['posts']) == desired_len

        # limit + offset + ordering
        for i in range(count + 10):  # offset
            for j in range(count + 10):  # limit
                r = self.request_and_expect_status("GET",
                                                   f"/api/{resource_type}/{resource_id}?offset={i}&limit={j + 1}&order=asc",
                                                   200)

                desired_len = min(min(j + 1, count), count - i)
                if i > count:
                    desired_len -= (count - i)

                assert len(r.json()['posts']) == desired_len

                self.assert_asc(r.json()['posts'], 'id')

        for i in range(count + 10):  # offset
            for j in range(count + 10):  # limit
                r = self.request_and_expect_status("GET",
                                                   f"/api/{resource_type}/{resource_id}?offset={i}&limit={j + 1}&order=desc",
                                                   200)

                desired_len = min(min(j + 1, count), count - i)
                if i > count:
                    desired_len -= (count - i)

                assert len(r.json()['posts']) == desired_len

                self.assert_desc(r.json()['posts'], 'id')

    def run(self):
        authors = ['a', 'b', 'c']
        tags = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
        total_posts = 0
        times = []
        posts_by_authors = {}.fromkeys(authors, 0)
        posts_by_tags = {}.fromkeys(tags, 0)

        for author in authors:
            for i in range(len(tags) - 2):
                total_posts += 1
                posts_by_authors[author] += 1
                posts_by_tags[tags[i]] += 1
                posts_by_tags[tags[i + 1]] += 1
                posts_by_tags[tags[i + 2]] += 1
                post = {
                    "author": author,
                    "text": f"alma #{tags[i]} #{tags[i + 1]} #{tags[i + 2]}"
                }
                r = self.request_and_expect_status("POST", "/api/post", 201, json=post)
                times.append(r.json()['created_at'])

        r = self.request_and_expect_status("GET", "/api/post", 200)
        assert len(r.json()) == total_posts

        r = self.request_and_expect_status("GET", "/api/author", 200)
        assert len(r.json()) == len(authors)

        r = self.request_and_expect_status("GET", "/api/tag", 200)
        assert len(r.json()) == len(tags)

        # and now, run some queries
        for i, a in enumerate(authors):
            self.do_magic("author", i + 1, posts_by_authors[a])

        for t in tags:
            self.do_magic("tag", t, posts_by_tags[t])


class FillFilter(TestCaseBase):
    def run(self):
        # Create some test posts

        authors = ['a', 'b', 'c']
        tags = ['a', 'b', 'c', 'd', 'e', 'f']
        total_posts = 0
        posts_by_authors = {}.fromkeys(authors, 0)
        posts_by_tags = {}.fromkeys(tags, 0)

        for author in authors:
            for i in range(len(tags) - 2):
                total_posts += 1
                posts_by_authors[author] += 1
                posts_by_tags[tags[i]] += 1
                posts_by_tags[tags[i + 1]] += 1
                posts_by_tags[tags[i + 2]] += 1
                post = {
                    "author": author,
                    "text": f"#{tags[i]} #{tags[i + 1]} #{tags[i + 2]}"
                }
                self.request_and_expect_status("POST", "/api/post", 201, json=post)

        r = self.request_and_expect_status("GET", "/api/post", 200)
        assert len(r.json()) == total_posts

        r = self.request_and_expect_status("GET", "/api/author", 200)
        assert len(r.json()) == len(authors)

        r = self.request_and_expect_status("GET", "/api/tag", 200)
        assert len(r.json()) == len(tags)

        # and now check if fill works or not
        for t in tags:
            r = self.request_and_expect_status("GET", f"/api/tag/{t}", 200)
            r2 = self.request_and_expect_status("GET", f"/api/tag/{t}?fill=true", 200)
            expect_json_tree(r.json(), r2.json())
            r3 = self.request_and_expect_status("GET", f"/api/tag/{t}?fill=false", 200)
            assert "posts" in r.json()
            assert "posts" not in r3.json()
            assert len(r.json()["posts"]) == posts_by_tags[t]

            self.request_and_expect_status("GET", f"/api/tag/{t}?fill=false&order=asc", 400)
            self.request_and_expect_status("GET", f"/api/tag/{t}?fill=false&order=desc", 400)
            self.request_and_expect_status("GET", f"/api/tag/{t}?fill=false&offset=1", 400)
            self.request_and_expect_status("GET", f"/api/tag/{t}?fill=false&limit=1", 400)
            self.request_and_expect_status("GET", f"/api/tag/{t}?fill=false&limit=1&offset=1", 400)
            self.request_and_expect_status("GET", f"/api/tag/{t}?fill=false&limit=1&offset=1&order=asc", 400)

        for i, a in enumerate(authors):
            r = self.request_and_expect_status("GET", f"/api/author/{i + 1}", 200)
            r2 = self.request_and_expect_status("GET", f"/api/author/{i + 1}?fill=true", 200)
            expect_json_tree(r.json(), r2.json())
            r3 = self.request_and_expect_status("GET", f"/api/author/{i + 1}?fill=false", 200)
            assert "posts" in r.json()
            assert "posts" not in r3.json()
            assert len(r.json()["posts"]) == posts_by_authors[a]

            self.request_and_expect_status("GET", f"/api/author/{a}?fill=false&order=asc", 400)
            self.request_and_expect_status("GET", f"/api/author/{a}?fill=false&order=desc", 400)
            self.request_and_expect_status("GET", f"/api/author/{a}?fill=false&offset=1", 400)
            self.request_and_expect_status("GET", f"/api/author/{a}?fill=false&limit=1", 400)
            self.request_and_expect_status("GET", f"/api/author/{a}?fill=false&limit=1&offset=1", 400)
            self.request_and_expect_status("GET", f"/api/author/{a}?fill=false&limit=1&offset=1&order=asc", 400)


class PaginateByIdAndLimit(TestCaseBase):

    @staticmethod
    def assert_asc(l: list, key):
        if len(l) > 0:
            if key:
                last_id = l[0][key]
            else:
                last_id = l[0]
            last_id -= 1
            for p in l:
                if key:
                    assert p[key] > last_id
                    last_id = p[key]
                else:
                    assert p > last_id
                    last_id = p

    @staticmethod
    def assert_desc(l: list, key):
        if len(l) > 0:
            if key:
                last_id = l[0][key]
            else:
                last_id = l[0]
            last_id += 1
            for p in l:
                if key:
                    assert p[key] < last_id
                    last_id = p[key]
                else:
                    assert p < last_id
                    last_id = p

    def run(self):
        # Create some test posts

        authors = ['a', 'b', 'c']
        tags = ['a', 'b', 'c', 'd', 'e', 'f']
        total_posts = 0
        posts_by_authors = {}.fromkeys(authors, 0)
        posts_by_tags = {}.fromkeys(tags, 0)

        for author in authors:
            for i in range(len(tags) - 2):
                for j in range(50):
                    total_posts += 1
                    posts_by_authors[author] += 1
                    posts_by_tags[tags[i]] += 1
                    posts_by_tags[tags[i + 1]] += 1
                    posts_by_tags[tags[i + 2]] += 1
                    post = {
                        "author": author,
                        "text": f"#{tags[i]} #{tags[i + 1]} #{tags[i + 2]} {j}"
                    }
                    self.request_and_expect_status("POST", "/api/post", 201, json=post)

        r = self.request_and_expect_status("GET", "/api/post", 200)
        assert len(r.json()) == total_posts

        r = self.request_and_expect_status("GET", "/api/author", 200)
        assert len(r.json()) == len(authors)

        r = self.request_and_expect_status("GET", "/api/tag", 200)
        assert len(r.json()) == len(tags)

        # simply paginate posts in various ways
        for order in [None, 'asc', 'desc']:
            for limit in range(1, total_posts + 5):
                last_id = None
                loaded_posts = 0
                while True:
                    query = f"/api/post?limit={limit}"

                    if order:
                        query += f"&order={order}"

                    if last_id is not None:
                        if order == 'desc':
                            query += f"&before_id={last_id}"
                        else:
                            query += f"&after_id={last_id}"

                    r = self.request_and_expect_status("GET", query, 200)

                    assert len(r.json()) <= limit

                    loaded_posts += len(r.json())
                    if last_id is not None:
                        for post in r.json():
                            if order == 'desc':
                                assert post['id'] < last_id
                            else:
                                assert post['id'] > last_id

                    if order == 'asc':
                        self.assert_asc(r.json(), 'id')

                    if order == 'desc':
                        self.assert_desc(r.json(), 'id')

                    decider = max
                    if order == 'desc':
                        decider = min

                    try:
                        last_id = decider(r.json(), key=lambda p: p['id'])['id']
                    except ValueError:
                        # empty list returned
                        pass

                    if len(r.json()) < limit:
                        # reached last page
                        break

                assert loaded_posts == total_posts

        for i, author in enumerate(authors):
            author_id = i + 1
            for order in [None, 'asc', 'desc']:
                for limit in range(1, total_posts + 5):
                    last_id = None
                    loaded_posts = 0
                    while True:
                        query = f"/api/post?author_id={author_id}&limit={limit}"

                        if order:
                            query += f"&order={order}"

                        if last_id is not None:
                            if order == 'desc':
                                query += f"&before_id={last_id}"
                            else:
                                query += f"&after_id={last_id}"

                        r = self.request_and_expect_status("GET", query, 200)

                        assert len(r.json()) <= limit

                        for post in r.json():
                            assert post['author']['id'] == author_id
                            assert post['author']['name'] == author

                        loaded_posts += len(r.json())
                        if last_id is not None:
                            for post in r.json():
                                if order == 'desc':
                                    assert post['id'] < last_id
                                else:
                                    assert post['id'] > last_id

                        if order == 'asc':
                            self.assert_asc(r.json(), 'id')

                        if order == 'desc':
                            self.assert_desc(r.json(), 'id')

                        decider = max
                        if order == 'desc':
                            decider = min

                        try:
                            last_id = decider(r.json(), key=lambda p: p['id'])['id']
                        except ValueError:
                            # empty list returned
                            pass

                        if len(r.json()) < limit:
                            # reached last page
                            break

                    assert loaded_posts == posts_by_authors[author]

        for tag in tags:
            for order in [None, 'asc', 'desc']:
                for limit in range(1, total_posts + 5):
                    last_id = None
                    loaded_posts = 0
                    while True:
                        query = f"/api/post?tag={tag}&limit={limit}"

                        if order:
                            query += f"&order={order}"

                        if last_id is not None:
                            if order == 'desc':
                                query += f"&before_id={last_id}"
                            else:
                                query += f"&after_id={last_id}"

                        r = self.request_and_expect_status("GET", query, 200)

                        assert len(r.json()) <= limit

                        for post in r.json():
                            assert tag in post['tags']

                        loaded_posts += len(r.json())
                        if last_id is not None:
                            for post in r.json():
                                if order == 'desc':
                                    assert post['id'] < last_id
                                else:
                                    assert post['id'] > last_id

                        if order == 'asc':
                            self.assert_asc(r.json(), 'id')

                        if order == 'desc':
                            self.assert_desc(r.json(), 'id')

                        decider = max
                        if order == 'desc':
                            decider = min

                        try:
                            last_id = decider(r.json(), key=lambda p: p['id'])['id']
                        except ValueError:
                            # empty list returned
                            pass

                        if len(r.json()) < limit:
                            # reached last page
                            break

                    assert loaded_posts == posts_by_tags[tag]

            # TODO: test with more than one author or tag


class LongPollRace(TestCaseBase):
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


class LongPollBasic(TestCaseBase):

    def run(self):
        polled_r: requests.Response | None = None

        post = {
            "author": "alma",
            "text": "alma"
        }

        def long_wait():
            nonlocal polled_r
            polled_r = self.request_and_expect_status("GET", "/api/poll?last=0", 200)

        t = threading.Thread(target=long_wait)
        t.start()
        time.sleep(1)

        r = self.request_and_expect_status("POST", "/api/post", 201, json=post)
        post_1 = r.json()

        t.join()
        assert len(polled_r.json()) == 1
        expect_json_tree(post_1, polled_r.json()[0])

        r = self.request_and_expect_status("POST", "/api/post", 201, json=post)
        post_2 = r.json()

        r = self.request_and_expect_status("GET", "/api/poll?last=0", 200)
        assert len(r.json()) == 2
        expect_json_tree([post_1, post_2], r.json())

        r = self.request_and_expect_status("GET", "/api/poll?last=1", 200)
        assert len(r.json()) == 1
        expect_json_tree([post_2], r.json())

        got_exc = False
        try:
            self.request_and_expect_status("GET", "/api/poll?last=2", 200, timeout=5)
        except requests.exceptions.Timeout:
            got_exc = True

        assert got_exc
