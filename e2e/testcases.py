import random
import string
import threading
import time

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
                "author": "a" * 33,
                "text": "alma"
            },
            {  # this is refused because it would evaluate to empty posts
                "author": "<img />",
                "text": "<script></script>"
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


class PostFiltersLocalBasic(TestCaseBase):
    def run(self):
        authors = ['a', 'b']
        tags = ['a', 'b', 'c', 'd', 'e']
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

        # simple ordering
        r = self.request_and_expect_status("GET", "/api/post?order=asc", 200)
        last_id = 0
        for post in r.json():
            assert post['id'] > last_id
            last_id = post['id']

        r = self.request_and_expect_status("GET", "/api/post?order=desc", 200)
        last_id = 999
        for post in r.json():
            assert post['id'] < last_id
            last_id = post['id']

        # limit checks
        for i in range(total_posts + 10):
            r = self.request_and_expect_status("GET", f"/api/post?limit={i + 1}", 200)
            assert len(r.json()) == min(i + 1, total_posts)

        # limit + ordering
        for i in range(total_posts + 10):
            r = self.request_and_expect_status("GET", f"/api/post?limit={i + 1}&order=asc", 200)
            assert len(r.json()) == min(i + 1, total_posts)
            last_id = 0
            for post in r.json():
                assert post['id'] > last_id
                last_id = post['id']

        for i in range(total_posts + 10):
            r = self.request_and_expect_status("GET", f"/api/post?limit={i + 1}&order=desc", 200)
            assert len(r.json()) == min(i + 1, total_posts)
            last_id = 999
            for post in r.json():
                assert post['id'] < last_id
                last_id = post['id']

        # TODO: offset


class LongPollRace(TestCaseBase):
    class LPReader(threading.Thread):
        def __init__(self, testcase):
            super().__init__()
            self.responses = set()
            self.errors = []
            self.running = True
            self.testcase: TestCaseBase = testcase
            self._remaining_passes = 2

        def run(self):
            last = 0
            while self._remaining_passes > 0:
                if not self.running:
                    self._remaining_passes -= 1

                if random.random() > 0.5:
                    time.sleep(random.random() * 0.01)

                try:
                    r = self.testcase.session.get("/api/poll?last=" + str(last), timeout=3)
                except requests.exceptions.Timeout:
                    continue

                if r.status_code == 204:
                    continue

                if r.status_code == 200:
                    for post in r.json():
                        post_id = post['id']
                        self.responses.add(post_id)
                        if post_id > last:
                            last = post_id
                else:
                    self.errors.append(r)

    def run(self):
        post = {
            "author": "alma",
            "text": "alma"
        }

        pollers = []
        for i in range(10):
            time.sleep(0.001)
            rd = self.LPReader(self)
            pollers.append(rd)
            rd.start()

        try:
            for i in range(500):
                if random.random() > 0.5:
                    time.sleep(random.random() * 0.001)
                self.request_and_expect_status("POST", "/api/post", 201, json=post)

        finally:
            for rd in pollers:
                rd.running = False

            for rd in pollers:
                rd.join()

            for rd in pollers:
                assert len(rd.responses) == 500
                assert len(rd.errors) == 0


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
