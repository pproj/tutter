import time
from datetime import datetime

from lib import TestCaseBase


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
