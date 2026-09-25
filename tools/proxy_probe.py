from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from time import perf_counter

import requests


@dataclass(frozen=True)
class ProbeResult:
    proxy: str
    ok: bool
    status_code: int | None
    latency_ms: int
    bytes_read: int
    speed_kbps: float
    error: str = ""

    def to_dict(self):
        return asdict(self)


def probe_proxy(proxy, target_url, timeout, max_bytes, valid_statuses):
    proxy_url = "http://%s" % proxy
    proxies = {"http": proxy_url, "https": proxy_url}
    headers = {}
    if max_bytes > 0:
        headers["Range"] = "bytes=0-%d" % (max_bytes - 1)

    started = perf_counter()
    bytes_read = 0
    try:
        with requests.get(
            target_url,
            headers=headers,
            proxies=proxies,
            timeout=timeout,
            stream=True,
            allow_redirects=False,
        ) as response:
            status_ok = response.status_code in valid_statuses
            if status_ok and max_bytes > 0:
                for chunk in response.iter_content(chunk_size=64 * 1024):
                    if not chunk:
                        continue
                    remaining = max_bytes - bytes_read
                    bytes_read += min(len(chunk), remaining)
                    if bytes_read >= max_bytes:
                        break

            elapsed = max(perf_counter() - started, 0.001)
            speed_kbps = round(bytes_read / 1024 / elapsed, 2) if bytes_read else 0.0
            error = "" if status_ok else "unexpected status %s" % response.status_code
            return ProbeResult(
                proxy=proxy,
                ok=status_ok,
                status_code=response.status_code,
                latency_ms=round(elapsed * 1000),
                bytes_read=bytes_read,
                speed_kbps=speed_kbps,
                error=error,
            )
    except requests.RequestException as exc:
        elapsed = max(perf_counter() - started, 0.001)
        return ProbeResult(
            proxy=proxy,
            ok=False,
            status_code=None,
            latency_ms=round(elapsed * 1000),
            bytes_read=bytes_read,
            speed_kbps=0.0,
            error=str(exc),
        )


def probe_many(proxies, target_url, timeout=10, max_bytes=0,
               valid_statuses=(200,), workers=20):
    if workers < 1:
        raise ValueError("workers must be at least 1")

    results = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(
                probe_proxy,
                proxy,
                target_url,
                timeout,
                max_bytes,
                frozenset(valid_statuses),
            ): proxy
            for proxy in proxies
        }
        for future in as_completed(futures):
            results.append(future.result())
    return results
