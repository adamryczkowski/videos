"""Unit tests for common.py utilities."""

from videos.common import DEFAULT_BROWSER, DEFAULT_BROWSER_PROFILE, build_cookie_opts


class TestBuildCookieOpts:
    def test_returns_cookiefile_when_set(self):
        result = build_cookie_opts(cookies_file="/path/to/cookies.txt")
        assert result == {"cookiefile": "/path/to/cookies.txt"}

    def test_returns_browser_when_no_cookies_file(self):
        result = build_cookie_opts()
        assert result == {
            "cookiesfrombrowser": (DEFAULT_BROWSER, DEFAULT_BROWSER_PROFILE, None, None)
        }

    def test_returns_browser_when_cookies_file_is_none(self):
        result = build_cookie_opts(cookies_file=None)
        assert result == {
            "cookiesfrombrowser": (DEFAULT_BROWSER, DEFAULT_BROWSER_PROFILE, None, None)
        }

    def test_custom_browser(self):
        result = build_cookie_opts(browser="chrome", browser_profile=None)
        assert result == {"cookiesfrombrowser": ("chrome", None, None, None)}

    def test_cookies_file_takes_priority_over_browser(self):
        result = build_cookie_opts(cookies_file="/cookies.txt", browser="chrome")
        assert result == {"cookiefile": "/cookies.txt"}
