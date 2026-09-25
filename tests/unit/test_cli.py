# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     test_cli.py
   Description :   proxyPool CLI 单元测试
   Author :        JHao
   date：          2026/6/15
-------------------------------------------------
     Change Activity:
                     2026/06/15:
-------------------------------------------------
"""
__author__ = 'JHao'

import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from proxyPool import cli
from setting import VERSION
from helper.proxy import Proxy
from tools.proxy_probe import ProbeResult


@pytest.fixture
def runner():
    return CliRunner()


class TestCli:

    def test_version_flag(self, runner):
        """--version 显示版本号"""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert VERSION in result.output

    @patch("proxyPool.startScheduler")
    def test_schedule_command(self, mock_scheduler, runner):
        """schedule 命令调用 startScheduler"""
        result = runner.invoke(cli, ["schedule"])
        assert result.exit_code == 0
        mock_scheduler.assert_called_once()

    @patch("proxyPool.startServer")
    def test_server_command(self, mock_server, runner):
        """server 命令调用 startServer"""
        result = runner.invoke(cli, ["server"])
        assert result.exit_code == 0
        mock_server.assert_called_once()

    @patch("handler.configHandler.ConfigHandler")
    @patch("helper.fetch._discover_fetchers")
    def test_fetcher_command(self, mock_discover, mock_conf_cls, runner):
        """fetcher 命令输出启用的代理源列表"""
        mock_cls1 = MagicMock()
        mock_cls1.name = "freeProxy01"
        mock_cls2 = MagicMock()
        mock_cls2.name = "freeProxy02"
        mock_discover.return_value = [mock_cls1, mock_cls2]
        mock_conf = MagicMock()
        mock_conf.fetcherExclude = []
        mock_conf_cls.return_value = mock_conf

        result = runner.invoke(cli, ["fetcher"])
        assert result.exit_code == 0
        assert "freeProxy01" in result.output
        assert "freeProxy02" in result.output

    @patch("handler.proxyHandler.ProxyHandler")
    def test_export_command(self, mock_handler_cls, runner):
        mock_handler_cls.return_value.getAll.return_value = [
            Proxy("1.2.3.4:8080", source="test")
        ]

        result = runner.invoke(cli, ["export"])

        assert result.exit_code == 0
        assert result.output == "1.2.3.4:8080\n"

    @patch("tools.proxy_probe.probe_many")
    @patch("handler.proxyHandler.ProxyHandler")
    def test_probe_command(self, mock_handler_cls, mock_probe_many, runner):
        mock_handler_cls.return_value.getAll.return_value = [
            Proxy("1.2.3.4:8080", source="test")
        ]
        mock_probe_many.return_value = [
            ProbeResult("1.2.3.4:8080", True, 200, 120, 0, 0.0)
        ]

        result = runner.invoke(cli, ["probe", "--target", "https://example.com"])

        assert result.exit_code == 0
        assert "1 passed" in result.output
        mock_probe_many.assert_called_once()
