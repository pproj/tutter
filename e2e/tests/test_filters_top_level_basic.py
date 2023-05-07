from datetime import datetime

from lib import TestCaseBase


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
