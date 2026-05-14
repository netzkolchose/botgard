from .base import *

from tools.urls import full_url, full_server_url


class TestTools(TestBase):

    def test_full_server_url(self):
        host = settings.FULL_SERVER_HOST
        self.assertEqual(f"{host}/some/path", full_server_url("some/path"))
        self.assertEqual(f"{host}/some/path", full_server_url("/some/path"))
        self.assertEqual(f"{host}/some/path?query=param", full_server_url("/some/path?query=param"))
        self.assertEqual(f"{host}/some/path", full_server_url("ftp://other-host.com/some/path"))
