from lib.json_tree_validate import expect_json_tree
from lib import TestCaseBase


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
