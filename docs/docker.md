# Docker 部署

## 使用 Docker Compose

本地整合版使用 Python 3.11 和 Redis 7，默认只监听宿主机 `127.0.0.1:5010`。Redis 不暴露宿主机端口，并通过命名卷持久化数据。

启动：

```console
docker compose up -d --build
```

查看状态和日志：

```console
docker compose ps
docker compose logs -f proxy_pool
```

停止服务但保留 Redis 数据：

```console
docker compose down
```

复制 `.env.example` 为 `.env` 后可调整绑定地址、端口、目标 URL 和有效状态码。只有确实需要局域网访问时，才将 `PROXY_POOL_BIND` 改为 `0.0.0.0`。

## 使用远程 Redis

直接运行镜像时，通过 `DB_CONN` 指定 Redis：

```console
docker build -t proxy-pool-local .
docker run --rm \
  -e DB_CONN=redis://:password@redis.example.com:6379/0 \
  -p 127.0.0.1:5010:5010 \
  proxy-pool-local
```

## 容器环境注意事项

在 Docker 容器中，建议使用前台模式启动服务：

```console
./proxy_pool.sh start --fg
```

Dockerfile 中的 ENTRYPOINT 配置：

```dockerfile
ENTRYPOINT ["tini", "--"]
CMD ["bash", "proxy_pool.sh", "start", "--fg"]
```

Compose 已为 Redis 和 API 配置健康检查。API 健康检查调用 `/count/`，因此容器显示 `healthy` 代表 API 与 Redis 均可访问。
