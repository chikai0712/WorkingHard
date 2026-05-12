FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# 安裝完整 BIND9 + 常用工具（dig/nslookup/ping/curl）
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
     bind9 bind9-utils dnsutils iputils-ping ca-certificates curl \
  && rm -rf /var/lib/apt/lists/*

# 建立 BIND 需要的目錄（會被 volume 覆蓋，但先確保存在）
RUN mkdir -p /etc/bind /etc/bind/zones /var/cache/bind /var/log/bind

# 以 foreground 執行，方便 docker logs 觀察
CMD ["named", "-g", "-c", "/etc/bind/named.conf"]

