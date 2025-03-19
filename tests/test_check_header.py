"""
Author: Daniel Wood | 2025-03-18
Modular Attack Surface Analysis Tool
License: Apache 2.0 - https://www.apache.org/licenses/LICENSE-2.0
LinkedIn: https://www.linkedin.com/in/danielewood
GitHub: https://github.com/automatesecurity
"""
import pytest
from scanners.web_scanner import check_header, check_server

# DummyResponse simulates an aiohttp response object.
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

# Updated DummySession: get is defined as a regular method returning DummyResponse.
class DummySession:
    def __init__(self, headers, raise_exception=False):
        self.headers = headers
        self.raise_exception = raise_exception

    def get(self, url, timeout):
        if self.raise_exception:
            raise Exception("Test exception")
        return DummyResponse(self.headers)

@pytest.mark.asyncio
async def test_check_header_x_xss_protection_present():
    """Verify check_header returns the X-XSS-Protection value when present."""
    dummy_session = DummySession(headers={"X-XSS-Protection": "1; mode=block"})
    result = await check_header(dummy_session, "http://example.com", "X-XSS-Protection")
    assert result == "1; mode=block"

@pytest.mark.asyncio
async def test_check_header_hsts_valid():
    """Verify check_header returns the correct HSTS header when present."""
    # Here we set a valid HSTS header
    dummy_session = DummySession(headers={"Strict-Transport-Security": "max-age=31536000; includeSubDomains"})
    # Use the proper header name for HSTS
    result = await check_header(dummy_session, "http://example.com", "Strict-Transport-Security")
    assert result == "max-age=31536000; includeSubDomains"

@pytest.mark.asyncio
async def test_check_header_x_frame_options_present():
    """Verify check_header returns the X-Frame-Options value when present."""
    dummy_session = DummySession(headers={"X-Frame-Options": "DENY"})
    result = await check_header(dummy_session, "http://example.com", "X-Frame-Options")
    assert result == "DENY"

@pytest.mark.asyncio
async def test_check_header_csp_present():
    """Verify check_header returns the CSP value when present."""
    dummy_session = DummySession(headers={"CSP": "default-src 'self'"})
    result = await check_header(dummy_session, "http://example.com", "CSP")
    assert result == "default-src 'self'"

@pytest.mark.asyncio
async def test_check_header_exception():
    """Verify check_header returns None when an exception is raised."""
    dummy_session = DummySession(headers={}, raise_exception=True)
    result = await check_header(dummy_session, "http://example.com", "X-XSS-Protection")
    assert result is None

@pytest.mark.asyncio
async def test_check_server_present():
    """Verify check_server returns the correct Server header when present."""
    dummy_session = DummySession(headers={"Server": "Apache/2.4.41 (Debian)"})
    result = await check_server(dummy_session, "http://example.com")
    assert result == "Apache/2.4.41 (Debian)"
