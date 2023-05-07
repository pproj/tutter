from lib import TestCaseBase


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
        self.request_and_expect_status(
            "GET",
            f"/api/post?after=2023-03-29T01:01:10%2b02:00&before=2023-03-28T01:01:10%2b02:00",
            400
        )
        self.request_and_expect_status(
            "GET",
            f"/api/post?after=2023-03-28T01:01:10%2b02:00&before=2023-03-28T01:01:10%2b02:00",
            400
        )
        self.request_and_expect_status("GET", f"/api/post?after_id=12&before_id=9", 400)
        self.request_and_expect_status("GET", f"/api/post?after_id=9&before_id=9", 400)

        # tag can not be empty string
        self.request_and_expect_status("GET", f"/api/post?tag=", 400)
        self.request_and_expect_status("GET", f"/api/post?tag=&tag=&tag=", 400)

        # username can not be empty string
        self.request_and_expect_status("GET", f"/api/author?name=", 400)
        self.request_and_expect_status("GET", f"/api/author?name=&name=&name=", 400)

        # poll have some filters too
        self.request_and_expect_status("GET", f"/api/poll?last=-1", 400, timeout=3)
        self.request_and_expect_status("GET", f"/api/poll?last=asdasd", 400, timeout=3)
        # self.request_and_expect_status("GET", f"/api/poll?last=", 400, timeout=3) # TODO

        self.request_and_expect_status("GET", f"/api/poll?author_id=-1", 400, timeout=3)
        # self.request_and_expect_status("GET", f"/api/poll?author_id=1&author_id=2", 400, timeout=3) # TODO
        self.request_and_expect_status("GET", f"/api/poll?author_id=asd", 400, timeout=3)

        self.request_and_expect_status("GET", f"/api/poll?tag=", 400, timeout=3)
        #         self.request_and_expect_status("GET", f"/api/poll?tag=asd&tag=asd2", 400, timeout=3) # TODO

        self.request_and_expect_status("GET", f"/api/poll?last=10&author_id=-1", 400, timeout=3)
        self.request_and_expect_status("GET", f"/api/poll?last=-10&author_id=-1", 400, timeout=3)
        self.request_and_expect_status("GET", f"/api/poll?last=10&author_id=asd", 400, timeout=3)
        self.request_and_expect_status("GET", f"/api/poll?last=asdasd&author_id=asd", 400, timeout=3)
        self.request_and_expect_status("GET", f"/api/poll?last=asdasd&author_id=asd", 400, timeout=3)
        self.request_and_expect_status("GET", f"/api/poll?last=asdasd&author_id=asd&tag=", 400, timeout=3)
