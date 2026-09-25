# 配置参考

配置文件 `setting.py` 位于项目的主目录下，配置主要分为五类：**服务配置**、**数据库配置**、**采集配置**、**校验配置**、**调度配置**。

## 服务配置

### `HOST`

API 服务监听的 IP。本机访问设置为 `127.0.0.1`，开启远程访问设置为 `0.0.0.0`。

- 默认值：`"127.0.0.1"`

该 API 包含删除、弹出代理等管理能力，默认不应直接暴露到公网。Docker Compose 会在容器内覆盖为 `0.0.0.0`，但宿主机端口仍默认只绑定 `127.0.0.1`。

### `PORT`

API 服务监听的端口。

- 默认值：`5010`

## 数据库配置

### `DB_CONN`

存放代理 IP 的数据库 URI，配置格式为：

```
db_type://[[user]:[pwd]]@ip:port/[db]
```

目前支持的 `db_type`：`redis`、`ssdb`。

配置示例：

```python
# Redis
DB_CONN = 'redis://@127.0.0.1:6379'
DB_CONN = 'redis://:123456@127.0.0.1:6379'
DB_CONN = 'redis://:123456@127.0.0.1:6379/15'

# SSDB
DB_CONN = 'ssdb://@127.0.0.1:8888'
DB_CONN = 'ssdb://:123456@127.0.0.1:8888'
```

### `TABLE_NAME`

存放代理的数据载体名称。SSDB 和 Redis 的存放结构为 hash。

- 默认值：`"use_proxy"`

## 采集配置

代理采集采用插件架构，调度器自动扫描 `fetcher/sources/` 目录，加载所有 `enabled=True` 的代理源。新增代理源只需在 `sources/` 下创建文件，无需修改配置。

查看当前启用的代理源：

```bash
python proxyPool.py fetcher
```

### `PROXY_FETCHER_EXCLUDE`

代理源黑名单。列表中的代理源 `name`（同时兼容旧的类名）不会被加载，即使 `enabled=True`。适用于临时禁用某个代理源而不修改其源文件。

```python
PROXY_FETCHER_EXCLUDE = [
    # "freevpnnode",
]
```

如需永久禁用，建议直接在源文件中设置 `enabled = False`。

## 校验配置

### `HTTP_URL`

用于检验代理是否可用的 IP 回显地址。

- 默认值：`"http://httpbin.org/ip"`

### `HTTPS_URL`

用于检验代理是否支持 HTTPS 的 IP 回显地址。

- 默认值：`"https://httpbin.org/ip"`

### `VERIFY_TIMEOUT`

检验代理的超时时间，单位秒。使用代理访问 `HTTP_URL` / `HTTPS_URL` 耗时超过 `VERIFY_TIMEOUT` 时，视为代理不可用。

- 默认值：`10`

### `VALID_STATUS_CODES`

目标站点返回这些 HTTP 状态码后，校验器才会继续检查响应正文和出口 IP；状态码本身不能证明代理可用。

- 默认值：`[200]`
- 环境变量格式：逗号分隔，例如 `VALID_STATUS_CODES=200,206,302,403`

### `VERIFY_PROXY_IP`

是否要求校验响应包含合法公网 IPv4，并且代理出口 IP 与本机直连出口不同。

- 默认值：`True`
- 环境变量：`VERIFY_PROXY_IP=true|false`

启用时，`HTTP_URL` 和 `HTTPS_URL` 必须是 IP 回显接口。无法获取直连出口、响应为空、无法解析公网 IP，或者出口 IP 没有变化时，代理均判定为不可用。直连出口会缓存 5 分钟，避免对每个候选代理重复请求。

仅当校验地址必须使用普通业务页面时才建议关闭；关闭后仍要求状态码符合配置且响应正文非空。

### `MAX_FAIL_COUNT`

检验代理允许的最大失败次数。超过则剔除代理。

- 默认值：`0`（即失败一次即删除）

### `POOL_SIZE_MIN`

代理检测定时任务运行前，若代理数量小于 `POOL_SIZE_MIN`，则先运行抓取程序。

- 默认值：`20`

## 代理属性

### `PROXY_REGION`

是否启用代理地域属性。开启后会尝试解析代理 IP 的地理位置信息。

- 默认值：`True`

## 调度配置

### `TIMEZONE`

调度器的时区设置。如果在虚拟机上运行时出现 `ValueError: Timezone offset does not match system offset` 错误，请设置该配置项。

- 默认值：`"Asia/Shanghai"`
