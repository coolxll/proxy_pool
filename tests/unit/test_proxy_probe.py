from unittest.mock import patch

import requests

from tools.proxy_probe import probe_proxy


class FakeResponse:
    def __init__(self, status_code=200, chunks=()):
        self.status_code = status_code
        self._chunks = chunks

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def iter_content(self, chunk_size):
        return iter(self._chunks)


@patch("tools.proxy_probe.requests.get")
def test_probe_proxy_uses_http_connect_proxy(mock_get):
    mock_get.return_value = FakeResponse(206, [b"a" * 1024, b"b" * 1024])

    result = probe_proxy("1.2.3.4:8080", "https://example.com", 3, 1536, {200, 206})

    assert result.ok is True
    assert result.bytes_read == 1536
    assert mock_get.call_args.kwargs["proxies"] == {
        "http": "http://1.2.3.4:8080",
        "https": "http://1.2.3.4:8080",
    }


@patch("tools.proxy_probe.requests.get")
def test_probe_proxy_rejects_unexpected_status(mock_get):
    mock_get.return_value = FakeResponse(500)

    result = probe_proxy("1.2.3.4:8080", "https://example.com", 3, 0, {200})

    assert result.ok is False
    assert result.status_code == 500


@patch("tools.proxy_probe.requests.get")
def test_probe_proxy_handles_request_error(mock_get):
    mock_get.side_effect = requests.exceptions.ProxyError("unreachable")

    result = probe_proxy("1.2.3.4:8080", "https://example.com", 3, 0, {200})

    assert result.ok is False
    assert result.status_code is None
    assert "unreachable" in result.error
