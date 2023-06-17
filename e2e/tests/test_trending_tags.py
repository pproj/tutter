from lib import TestCaseBase


class TestTrendingTags(TestCaseBase):

    def run(self):
        r = self.request_and_expect_status("GET", "/api/trending", 200)

        # by default, it should be empty
        assert not r.json()
        assert len(r.json()) == 0
        assert isinstance(r.json(), list)

        # create some tags
        tags = ['alma', 'barack', 'korte', 'szilva', 'meggy']
        post = {
            "author": "alma",
            "text": ""
        }
        for tag in tags:
            post["text"] += f"#{tag} "
        self.request_and_expect_status("POST", "/api/post", 201, json=post)

        should_be_trending = set()
        for tag in tags:
            should_be_trending.add(tag)
            self.set_trending_tag(tag, True)
            r = self.request_and_expect_status("GET", "/api/trending", 200)
            assert set(r.json()) == should_be_trending

        for tag in tags:
            should_be_trending.remove(tag)
            self.set_trending_tag(tag, False)
            r = self.request_and_expect_status("GET", "/api/trending", 200)
            assert set(r.json()) == should_be_trending
