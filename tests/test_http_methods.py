"""
Author: Daniel Wood | 2025-03-18
Modular Attack Surface Analysis Tool
License: Apache 2.0 - https://www.apache.org/licenses/LICENSE-2.0
LinkedIn: https://www.linkedin.com/in/danielewood
GitHub: https://github.com/automatesecurity
"""
import pytest
from scanners.web_scanner import check_http_methods

# Dummy response that supports async context management.
class DummyResponse:
    def __init__(self, headers):
        self._headers = headers

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    @property
    def headers(self):
        return self._headers

# Dummy session that simulates a successful OPTIONS response.
class DummySession:
    def options(self, url, timeout):
        headers = {"Allow": "GET, POST, PUT, DELETE, OPTIONS"}
        return DummyResponse(headers)

# Dummy session that simulates an OPTIONS response with no Allow header.
class DummySessionNoAllow:
    def options(self, url, timeout):
        headers = {}
        return DummyResponse(headers)

# Dummy session that raises an exception when options() is called.
class DummySessionException:
    def options(self, url, timeout):
        raise Exception("Test exception in options()")

@pytest.mark.asyncio
async def test_check_http_methods_normal():
    dummy_session = DummySession()
    url = "http://example.com"
    methods = await check_http_methods(dummy_session, url)
    # We expect the returned list to contain the HTTP methods in uppercase, stripped of whitespace.
    expected = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    assert methods == expected

@pytest.mark.asyncio
async def test_check_http_methods_no_allow():
    dummy_session = DummySessionNoAllow()
    url = "http://example.com"
    methods = await check_http_methods(dummy_session, url)
    # When no Allow header is present, we expect an empty list.
    assert methods == []

@pytest.mark.asyncio
async def test_check_http_methods_exception():
    dummy_session = DummySessionException()
    url = "http://example.com"
    methods = await check_http_methods(dummy_session, url)
    # On exception, our function should return an empty list.
    assert methods == []
