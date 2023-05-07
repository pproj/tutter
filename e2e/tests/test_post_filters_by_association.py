from lib import TestCaseBase


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
