# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     testValidator.py
   Description :   formatValidator正则测试
   Author :        JHao
   date：          2026/5/28
-------------------------------------------------
   Change Activity:
                   2026/05/28:
-------------------------------------------------
"""
__author__ = 'JHao'

import re
import pytest
from unittest.mock import patch, MagicMock

import helper.validator as validator_mod
from helper.validator import (
    IP_REGEX,
    customValidatorExample,
    extractResponseIps,
    formatValidator,
    httpTimeOutValidator,
    httpsTimeOutValidator,
)


@pytest.fixture(autouse=True)
def validator_conf():
    """Use deterministic validation settings and isolate the direct-IP cache."""
    validator_mod._direct_ip_cache.clear()
    mock_conf = MagicMock(
        httpUrl="http://echo.test/ip",
        httpsUrl="https://echo.test/ip",
        verifyTimeout=3,
        validStatusCodes=(200,),
        verifyProxyIp=True,
    )
    with patch.object(validator_mod, "conf", mock_conf):
        yield mock_conf
    validator_mod._direct_ip_cache.clear()


def response(status=200, text='{"origin": "8.8.8.8"}'):
    mock = MagicMock(status_code=status, text=text)
    mock.content = text.encode("utf-8")
    return mock


class TestIPRegex:

    @pytest.mark.parametrize("proxy", [
        "1.2.3.4:8080",
        "192.168.1.1:3128",
        "10.0.0.1:80",
        "255.255.255.255:65535",
        "0.0.0.0:1",
        "1.2.3.4:99999",   # regex 不校验端口范围
        "999.1.1.1:80",    # regex 不校验 IP 范围
        "user:pass@1.2.3.4:8080",
        "admin:secret@192.168.1.1:443",
    ])
    def test_valid_proxy_format(self, proxy):
        assert IP_REGEX.fullmatch(proxy) is not None, f"应匹配: {proxy}"

    @pytest.mark.parametrize("proxy", [
        "",
        "abc",
        "1.2.3.4",
        "1.2.3.4:",
        ":8080",
        "1.2.3.4:abc",
        "1.2.3.4:8080:extra",
        "host:8080",
    ])
    def test_invalid_proxy_format(self, proxy):
        assert IP_REGEX.fullmatch(proxy) is None, f"不应匹配: {proxy}"


class TestFormatValidator:

    @pytest.mark.parametrize("proxy", [
        "1.2.3.4:8080",
        "192.168.1.1:3128",
        "user:pass@10.0.0.1:80",
    ])
    def test_valid_returns_true(self, proxy):
        assert formatValidator(proxy) is True

    @pytest.mark.parametrize("proxy", [
        "",
        "abc",
        "1.2.3.4",
        "999.1.1.1:80",
        "1.2.3.4:99999",
        "1.2.3.4:0",
    ])
    def test_invalid_returns_false(self, proxy):
        assert formatValidator(proxy) is False


class TestExtractResponseIps:

    def test_extracts_public_ips_from_json_response(self):
        result = extractResponseIps(response(text='{"origin": "8.8.8.8, 1.1.1.1"}'))
        assert result == ("8.8.8.8", "1.1.1.1")

    def test_ignores_private_and_invalid_ips(self):
        result = extractResponseIps(response(text='{"origin": "192.168.1.1, 999.1.1.1"}'))
        assert result == ()


class TestHttpTimeOutValidator:
    """httpTimeOutValidator 测试"""

    @patch("helper.validator._directResponseIps", return_value=("1.1.1.1",))
    @patch("helper.validator.get")
    def test_returns_true_for_real_response_with_changed_exit_ip(self, mock_get, mock_direct):
        mock_get.return_value = response()
        assert httpTimeOutValidator("1.2.3.4:8080") is True
        assert mock_get.call_args.kwargs["proxies"]["https"] == "http://1.2.3.4:8080"

    @patch("helper.validator._directResponseIps", return_value=("8.8.8.8",))
    @patch("helper.validator.get")
    def test_returns_false_when_exit_ip_did_not_change(self, mock_get, mock_direct):
        mock_get.return_value = response()
        assert httpTimeOutValidator("1.2.3.4:8080") is False

    @patch("helper.validator.get")
    def test_returns_false_on_empty_response(self, mock_get):
        mock_get.return_value = response(text="")
        assert httpTimeOutValidator("1.2.3.4:8080") is False

    @patch("helper.validator.get")
    def test_returns_false_on_non_200(self, mock_get):
        mock_get.return_value = response(status=502)
        assert httpTimeOutValidator("1.2.3.4:8080") is False

    @patch("helper.validator.get")
    def test_returns_false_on_exception(self, mock_get):
        mock_get.side_effect = TimeoutError("connection timed out")
        assert httpTimeOutValidator("1.2.3.4:8080") is False

    @patch("helper.validator.get")
    def test_can_disable_ip_comparison_but_still_requires_content(
            self, mock_get, validator_conf):
        validator_conf.verifyProxyIp = False
        mock_get.return_value = response(text="ordinary response")
        assert httpTimeOutValidator("1.2.3.4:8080") is True


class TestHttpsTimeOutValidator:
    """httpsTimeOutValidator 测试"""

    @patch("helper.validator._directResponseIps", return_value=("1.1.1.1",))
    @patch("helper.validator.get")
    def test_returns_true_for_real_https_response(self, mock_get, mock_direct):
        mock_get.return_value = response()
        assert httpsTimeOutValidator("1.2.3.4:8080") is True
        call_kwargs = mock_get.call_args
        assert call_kwargs[1]["verify"] is True
        assert call_kwargs[1]["proxies"]["https"] == "http://1.2.3.4:8080"

    @patch("helper.validator.get")
    def test_returns_false_on_non_200(self, mock_get):
        mock_get.return_value = response(status=502)
        assert httpsTimeOutValidator("1.2.3.4:8080") is False

    @patch("helper.validator.get")
    def test_returns_false_on_exception(self, mock_get):
        mock_get.side_effect = TimeoutError("connection timed out")
        assert httpsTimeOutValidator("1.2.3.4:8080") is False


class TestDirectResponseIps:

    @patch("helper.validator.get")
    def test_caches_direct_exit_ip(self, mock_get):
        mock_get.return_value = response()
        first = validator_mod._directResponseIps("https://echo.test/ip", False)
        second = validator_mod._directResponseIps("https://echo.test/ip", False)
        assert first == ("8.8.8.8",)
        assert second == first
        mock_get.assert_called_once()


class TestCustomValidatorExample:
    """customValidatorExample 测试"""

    def test_always_returns_true(self):
        """customValidatorExample 始终返回 True"""
        assert customValidatorExample("1.2.3.4:8080") is True
