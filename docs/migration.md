# 本地项目整合说明

工作区内原有四类代理相关项目，职责存在重叠：

| 原目录 | 原职责 | 整合后的处理 |
|---|---|---|
| `proxy_pool` | 抓取、校验、Redis 存储、API | 作为唯一主项目继续维护 |
| `ProxyPool` | 另一套抓取、校验、Redis、API 实现 | 保留作参考，不再作为部署入口 |
| `proxySpeedTest` | 从文本文件读取代理并下载测速 | 由 `proxyPool.py probe --max-bytes` 替代 |
| `ProxyTester` | 针对目标站点测试、导入 Redis、维护已用代理 | 目标测试由 `probe` 替代；代理数据统一由主项目 Redis 管理 |

## 整合原则

1. 只保留一套抓取器、调度器、数据库结构和 HTTP API，避免两套服务争用 Redis 或产生不同评分结果。
2. 通用健康检查保持轻量，不再为每个代理自动下载 1 MB 文件。
3. 目标站点验证和速度测试改为显式 CLI 操作，只有需要时才运行。
4. Redis 地址、目标 URL、有效状态码都通过环境变量配置，不在源码中写死内网地址。
5. 原目录暂不删除；稳定运行一段时间后再归档，便于回查旧逻辑。

## 功能迁移

### 导出代理

```bash
python proxyPool.py export --https-only -o proxies.txt
```

也可以通过 API 导出：

```text
GET /export/?type=https
```

### 针对目标站点验证

```bash
python proxyPool.py probe \
  --https-only \
  --target https://example.com \
  --status 200 \
  --status 403 \
  --output usable.txt \
  --json-report probe-report.json
```

### 显式测速

下面的命令最多通过每个代理读取 1 MiB，不创建临时下载文件：

```bash
python proxyPool.py probe \
  --https-only \
  --target https://speed.cloudflare.com/__down?bytes=1048576 \
  --max-bytes 1048576 \
  --min-kbps 100 \
  --output fast-proxies.txt
```

`--delete-failed` 只删除连接失败或状态码不符合要求的代理，不会因为低于 `--min-kbps` 自动删除。

## 旧配置迁移

- 原 `redis://192.168.3.66:6379/0` 改为环境变量 `DB_CONN`。
- 原 Keep2Share/Baidu 硬编码验证改为 `HTTP_URL`、`HTTPS_URL` 和 `VALID_STATUS_CODES`。
- 原 `/export/` 接口已保留，返回 `text/plain`，每行一个 `host:port`。
- 原 `startApiServer.py`、`startScheduler.py` 由 `python proxyPool.py server|schedule` 取代。

## 建议归档顺序

确认新服务连续运行并满足目标站点需求后：

1. 停止旧 `ProxyPool` 容器或进程。
2. 保留旧目录的 Git 历史，添加归档标记。
3. 删除旧虚拟环境、输出文件和重复 Redis 数据，而不是删除源码历史。
