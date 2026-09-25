# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     proxy_pool
   Description :   proxy pool 启动入口
   Author :        JHao
   date：          2020/6/19
-------------------------------------------------
   Change Activity:
                   2020/6/19:
-------------------------------------------------
"""
__author__ = 'JHao'

import click
from helper.launcher import startServer, startScheduler
from setting import BANNER, VERSION

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version=VERSION)
def cli():
    """ProxyPool cli工具"""


@cli.command(name="schedule")
def schedule():
    """ 启动调度程序 """
    click.echo(BANNER)
    startScheduler()


@cli.command(name="server")
def server():
    """ 启动api服务 """
    click.echo(BANNER)
    startServer()


@cli.command(name="fetcher")
def fetcher():
    """ 查看启用的代理源 """
    from helper.fetch import _discover_fetchers
    from handler.configHandler import ConfigHandler
    conf = ConfigHandler()
    exclude = conf.fetcherExclude
    fetcher_classes = _discover_fetchers(exclude)
    click.echo("Active fetchers (%d):" % len(fetcher_classes))
    for cls in fetcher_classes:
        click.echo("  - %s" % cls.name)
    if exclude:
        click.echo("\nExcluded: %s" % ", ".join(exclude))


@cli.command(name="export")
@click.option("--https-only", is_flag=True, help="Only export HTTPS-capable proxies.")
@click.option("-o", "--output", type=click.Path(dir_okay=False), help="Write to a file instead of stdout.")
def export_proxies(https_only, output):
    """Export proxies as one host:port per line."""
    from pathlib import Path
    from handler.proxyHandler import ProxyHandler

    proxies = ProxyHandler().getAll(https_only)
    body = "\n".join(proxy.proxy for proxy in proxies)
    if body:
        body += "\n"
    if output:
        Path(output).write_text(body, encoding="utf-8")
        click.echo("Exported %d proxies to %s" % (len(proxies), output))
    else:
        click.echo(body, nl=False)


@cli.command(name="probe")
@click.option("--target", help="Target URL. Defaults to HTTP_URL or HTTPS_URL.")
@click.option("--https-only", is_flag=True, help="Only probe HTTPS-capable proxies.")
@click.option("--timeout", type=click.IntRange(1), default=10, show_default=True)
@click.option("--workers", type=click.IntRange(1, 100), default=20, show_default=True)
@click.option("--limit", type=click.IntRange(0), default=100, show_default=True,
              help="Maximum proxies to check; 0 checks all proxies.")
@click.option("--max-bytes", type=click.IntRange(0), default=0, show_default=True,
              help="Read at most this many response bytes; use a positive value for speed testing.")
@click.option("--status", "valid_statuses", type=int, multiple=True,
              help="Accepted HTTP status. Repeat for multiple values.")
@click.option("--min-kbps", type=click.FloatRange(0), default=0.0, show_default=True)
@click.option("--delete-failed", is_flag=True, help="Delete connection/status failures from the pool.")
@click.option("-o", "--output", type=click.Path(dir_okay=False),
              help="Write passing proxies to a text file.")
@click.option("--json-report", type=click.Path(dir_okay=False),
              help="Write all detailed results to JSON.")
def probe(target, https_only, timeout, workers, limit, max_bytes,
          valid_statuses, min_kbps, delete_failed, output, json_report):
    """Check pool proxies against a target and optionally measure throughput."""
    import json
    from pathlib import Path

    from handler.configHandler import ConfigHandler
    from handler.proxyHandler import ProxyHandler
    from helper.proxy import Proxy
    from tools.proxy_probe import probe_many

    conf = ConfigHandler()
    target = target or (conf.httpsUrl if https_only else conf.httpUrl)
    statuses = valid_statuses or conf.validStatusCodes
    handler = ProxyHandler()
    proxy_objects = handler.getAll(https_only)
    if limit:
        proxy_objects = proxy_objects[:limit]

    results = probe_many(
        [proxy.proxy for proxy in proxy_objects],
        target_url=target,
        timeout=timeout,
        max_bytes=max_bytes,
        valid_statuses=statuses,
        workers=workers,
    )
    passing = [result for result in results if result.ok and result.speed_kbps >= min_kbps]

    if delete_failed:
        for result in results:
            if not result.ok:
                handler.delete(Proxy(result.proxy))

    if output:
        body = "\n".join(result.proxy for result in passing)
        Path(output).write_text(body + ("\n" if body else ""), encoding="utf-8")

    if json_report:
        Path(json_report).write_text(
            json.dumps([result.to_dict() for result in results], indent=2),
            encoding="utf-8",
        )

    ranked = sorted(results, key=lambda item: (item.ok, item.speed_kbps, -item.latency_ms), reverse=True)
    for result in ranked[:20]:
        state = "PASS" if result.ok and result.speed_kbps >= min_kbps else "FAIL"
        click.echo(
            "%-4s %-24s status=%-4s latency=%5dms speed=%8.2fKB/s %s" % (
                state,
                result.proxy,
                result.status_code if result.status_code is not None else "-",
                result.latency_ms,
                result.speed_kbps,
                result.error,
            )
        )
    click.echo("Checked %d proxies against %s; %d passed." % (len(results), target, len(passing)))


if __name__ == '__main__':
    cli()
