FROM python:3.11-slim

LABEL maintainer="jhao104 <j_hao104@163.com>"

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=Asia/Shanghai

COPY ./requirements.txt .

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends bash tini tzdata && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir --upgrade pip setuptools && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5010

ENTRYPOINT ["tini", "--"]
CMD ["bash", "proxy_pool.sh", "start", "--fg"]
