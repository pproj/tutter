from lib import TestCaseBase


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
            self.do_magic("author", str(i + 1), posts_by_authors[a])

        for t in tags:
            self.do_magic("tag", t, posts_by_tags[t])
