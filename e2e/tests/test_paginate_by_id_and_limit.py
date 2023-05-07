from lib import TestCaseBase


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
