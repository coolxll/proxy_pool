# 快速开始

## 下载代码

本地整合版要求 Python 3.10 或更高版本。下载代码后进入 `proxy_pool` 目录：

```console
git clone https://github.com/jhao104/proxy_pool.git
```

或者下载特定的 [release](https://github.com/jhao104/proxy_pool/releases) 版本。

## 安装依赖

到项目目录下使用 `pip` 安装依赖库：

```console
python -m pip install --upgrade pip setuptools
pip install -r requirements.txt
```

## 更新配置

配置文件 `setting.py` 位于项目的主目录下，常用的配置项：

```python
# API 服务
HOST = "0.0.0.0"               # 监听 IP
PORT = 5010                    # 监听端口

# 数据库
DB_CONN = 'redis://:pwdstring@127.0.0.1:6379/0'

# 可选：按代理源的 name 临时禁用抓取器
# 默认自动加载 fetcher/sources/ 下所有 enabled=True 的代理源
PROXY_FETCHER_EXCLUDE = ["freevpnnode"]
```

更多配置请参考 [配置参考](configuration.md)。

## 启动项目

完整程序包含两部分：`schedule` 调度程序和 `server` API 服务。调度程序负责采集和验证代理，API 服务提供代理服务 HTTP 接口。

### 方式一：使用 `proxy_pool.sh`（推荐）

`proxy_pool.sh` 提供统一的服务管理接口，支持后台运行和进程管理：

```console
# 后台启动所有服务（Linux/macOS）
./proxy_pool.sh start

# 前台启动（容器环境）
./proxy_pool.sh start --fg

# 停止服务
./proxy_pool.sh stop

# 查看状态
./proxy_pool.sh status

# 重启服务
./proxy_pool.sh restart
```

### 方式二：使用 `proxyPool.py`

`proxyPool.py` 是项目的 Python CLI 入口，可以分别启动调度程序和 API 服务：

```console
# 启动调度程序
python proxyPool.py schedule

# 启动 API 服务
python proxyPool.py server
```

在 Windows 上建议使用 Docker Compose，或在两个终端中分别运行上面的 `schedule` 和 `server` 命令。

### 导出、目标验证和测速

```console
# 导出 HTTPS 代理
python proxyPool.py export --https-only -o proxies.txt

# 对目标站点进行并发验证
python proxyPool.py probe --https-only --target https://example.com --status 200

# 最多读取 1 MiB 并按速度筛选
python proxyPool.py probe --target https://example.com/file.bin --max-bytes 1048576 --min-kbps 100
```

完整迁移关系见[本地项目整合说明](migration.md)。

## 服务管理

### proxy_pool.sh 可用命令

| 命令 | 说明 |
|------|------|
| `start` | 启动所有服务（默认后台运行） |
| `start --fg` | 前台启动，适用于容器环境 |
| `stop` | 停止所有服务 |
| `restart` | 重启所有服务 |
| `status` | 查看服务运行状态 |

### PID 文件

服务启动后会在项目根目录生成 `proxy_pool.pid` 文件，记录所有子进程的 PID。该文件用于 `stop` 命令识别需要终止的进程、`status` 命令检查进程状态、防止重复启动。`stop` 命令执行后会自动删除该文件。

## 故障排除

### 服务启动失败

使用前台启动查看详细日志排查错误：

```console
./proxy_pool.sh start --fg
```

### 端口被占用

修改 `setting.py` 中的 `PORT` 配置：

```python
PORT = 5010  # 修改为其他端口
```

### 无法停止服务

手动终止进程：

```console
# 查看 PID 文件
cat proxy_pool.pid

# 手动终止进程
kill <PID>

# 删除 PID 文件
rm proxy_pool.pid
```

## 运行测试

### 安装测试依赖

```console
pip install -r requirements-test.txt
```

### 运行全部测试

```console
pytest
```

### 分层运行

```console
# 单元测试（零外部依赖，CI 必跑）
pytest tests/unit/

# API 路由测试
pytest tests/api/

# 集成测试（RedisClient/SsdbClient CRUD，使用 fakeredis 模拟）
pytest tests/integration/
```

### 查看覆盖率

```console
pytest --cov=. --cov-report=term-missing
```
