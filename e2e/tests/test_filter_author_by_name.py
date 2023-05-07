from lib import TestCaseBase


class FilterAuthorByName(TestCaseBase):
    def run(self):
        existing_names = [
            "alma",
            "barack",
            "korte",
            "szilva"
        ]
        non_existing_names = [
            "narancs",
            "eper",
            "banan"
        ]
        all_names = existing_names + non_existing_names

        for name in existing_names:
            post = {
                "author": name,
                "text": "a"
            }
            r = self.request_and_expect_status("POST", "/api/post", 201, json=post)
            assert r.json()['author']['name'] == name

        # single test
        for name in all_names:
            r = self.request_and_expect_status("GET", f"/api/author?name={name}", 200)
            if name in existing_names:
                assert len(r.json()) == 1
                assert r.json()[0]['name'] == name
            else:
                assert len(r.json()) == 0

        # multi test
        for i in range(len(all_names)):
            for j in range(i, len(all_names)):
                choosen_names = all_names[i:j]
                if not choosen_names:
                    continue

                query_text = '?name=' + '&name='.join(choosen_names)
                r = self.request_and_expect_status("GET", f"/api/author" + query_text, 200)

                expected_names = 0
                for name in choosen_names:
                    if name in existing_names:
                        expected_names += 1

                assert len(r.json()) == expected_names

                for author in r.json():
                    name = author['name']
                    assert name in choosen_names
                    assert name in existing_names
