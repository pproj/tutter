import os
from abc import ABC, abstractmethod

import psycopg2
import requests
from requests_toolbelt.sessions import BaseUrlSession

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8080")
DEBUG_PIN = os.environ["DEBUG_PIN"] # crash if undefined


class UnexpectedHTTPStatus(Exception):
    def __init__(self, url: str, expected: int, got: int):
        pass


class TestCaseBase(ABC):

    priority = 0

    def __init__(self):
        self.base_url = BASE_URL
        self.session = BaseUrlSession(self.base_url)

    def __call__(self, *args, **kwargs):
        self.reset_database()
        try:
            self.run()
        finally:
            self.reset_database()

    @abstractmethod
    def run(self):
        pass

    def request_and_expect_status(self, method: str, url: str, expected_status: int,
                                  # I know, I could just use args,kwargs, but I wanted my IDE to have proper hints
                                  params=None,
                                  data=None,
                                  headers=None,
                                  cookies=None,
                                  files=None,
                                  auth=None,
                                  timeout=None,
                                  allow_redirects=True,
                                  proxies=None,
                                  hooks=None,
                                  stream=None,
                                  verify=None,
                                  cert=None,
                                  json=None
                                  ) -> requests.Response:
        r = self.session.request(method, url, params=params, data=data, headers=headers, cookies=cookies, files=files,
                                 auth=auth, timeout=timeout, allow_redirects=allow_redirects, proxies=proxies,
                                 hooks=hooks, stream=stream, verify=verify, cert=cert, json=json)

        if r.status_code != expected_status:
            raise UnexpectedHTTPStatus(url, expected_status, r.status_code)

        return r

    def reset_database(self):
        headers = {
            "X-Debug-Pin": DEBUG_PIN
        }
        r = self.session.post("/api/debug/cleanup", headers=headers)
        r.raise_for_status()
