# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     _validators
   Description :   定义proxy验证方法
   Author :        JHao
   date：          2021/5/25
-------------------------------------------------
   Change Activity:
                   2023/03/10: 支持带用户认证的代理格式 username:password@ip:port
-------------------------------------------------
"""
__author__ = 'JHao'

import ipaddress
import re
from threading import Lock
from time import monotonic

from requests import get
from util.six import withMetaclass
from util.singleton import Singleton
from handler.configHandler import ConfigHandler

conf = ConfigHandler()

HEADER = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0',
          'Accept': '*/*',
          'Connection': 'keep-alive',
          'Accept-Language': 'zh-CN,zh;q=0.8'}

IP_REGEX = re.compile(r"(.*:.*@)?\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}")
IP_RESPONSE_REGEX = re.compile(r"(?<![\d.])\d{1,3}(?:\.\d{1,3}){3}(?![\d.])")

_direct_ip_cache = {}
_direct_ip_lock = Lock()
_DIRECT_IP_CACHE_TTL = 300


def extractResponseIps(response):
    """Return the public IPv4 addresses found in an IP echo response."""
    text = response.text or ""
    result = []
    for candidate in IP_RESPONSE_REGEX.findall(text):
        try:
            address = ipaddress.ip_address(candidate)
        except ValueError:
            continue
        if address.version == 4 and address.is_global:
            normalized = str(address)
            if normalized not in result:
                result.append(normalized)
    return tuple(result)


def _directResponseIps(url, verify):
    """Get and briefly cache this process's direct public exit IPs."""
    key = (url, verify)
    now = monotonic()
    with _direct_ip_lock:
        cached = _direct_ip_cache.get(key)
        if cached and now - cached[0] < _DIRECT_IP_CACHE_TTL:
            return cached[1]
        try:
            response = get(
                url,
                headers=HEADER,
                timeout=conf.verifyTimeout,
                verify=verify,
            )
            ips = extractResponseIps(response) if response.status_code in conf.validStatusCodes else ()
        except Exception:
            ips = ()
        _direct_ip_cache[key] = (now, ips)
        return ips


def _proxyResponseValidator(proxy, url, verify):
    proxy_url = "http://{proxy}".format(proxy=proxy)
    proxies = {"http": proxy_url, "https": proxy_url}
    try:
        response = get(
            url,
            headers=HEADER,
            proxies=proxies,
            timeout=conf.verifyTimeout,
            verify=verify,
        )
        if response.status_code not in conf.validStatusCodes or not response.content:
            return False
        if not conf.verifyProxyIp:
            return True

        proxy_ips = set(extractResponseIps(response))
        direct_ips = set(_directResponseIps(url, verify))
        return bool(proxy_ips and direct_ips and proxy_ips - direct_ips)
    except Exception:
        return False


class ProxyValidator(withMetaclass(Singleton)):
    pre_validator = []
    http_validator = []
    https_validator = []

    @classmethod
    def addPreValidator(cls, func):
        cls.pre_validator.append(func)
        return func

    @classmethod
    def addHttpValidator(cls, func):
        cls.http_validator.append(func)
        return func

    @classmethod
    def addHttpsValidator(cls, func):
        cls.https_validator.append(func)
        return func


@ProxyValidator.addPreValidator
def formatValidator(proxy):
    """检查代理格式"""
    if not IP_REGEX.fullmatch(proxy):
        return False

    endpoint = proxy.rsplit('@', 1)[-1]
    host, port = endpoint.rsplit(':', 1)
    try:
        ipaddress.ip_address(host)
        return 1 <= int(port) <= 65535
    except ValueError:
        return False


@ProxyValidator.addHttpValidator
def httpTimeOutValidator(proxy):
    """Require a real HTTP response and, by default, a changed public exit IP."""
    return _proxyResponseValidator(proxy, conf.httpUrl, verify=True)


@ProxyValidator.addHttpsValidator
def httpsTimeOutValidator(proxy):
    """Require a real HTTPS response and, by default, a changed public exit IP."""
    return _proxyResponseValidator(proxy, conf.httpsUrl, verify=True)


@ProxyValidator.addHttpValidator
def customValidatorExample(proxy):
    """自定义validator函数，校验代理是否可用, 返回True/False"""
    return True
