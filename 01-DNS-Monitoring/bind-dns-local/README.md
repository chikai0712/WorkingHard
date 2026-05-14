# 本機 BIND DNS 專案

在本機（macOS/Linux）以 Docker 搭建 BIND 9 權威／遞迴 DNS，供開發與測試使用。

## 設計

- **BIND 9（完整 Ubuntu）**：以 `ubuntu:22.04` 為基底，用 apt 安裝 `bind9` 與常用工具（`dig/nslookup/ping/curl`），避免精簡映像缺工具。
- **角色**：可當作本機權威 DNS（自訂 zone）或遞迴解析器（含 root hints）。
- **目錄**：
  - `config/`：`named.conf`、`named.conf.local`、localhost/root 等基礎 zone 檔；自訂 zone 放在 `config/zones/`（如 `db.example.com`）。
  - `cache/`：BIND 快取（容器掛載用）。
  - `logs/`：BIND 日誌（可選掛載）。
- **埠口**：容器對外 53/udp、53/tcp，本機以 `127.0.0.1:53` 查詢。

## 需求

- Docker 與 Docker Compose
- 本機 53 埠未被佔用（若被系統 DNS 佔用，請先停用或改用其他埠）

## 快速開始

```bash
cd bind-dns-local
./scripts/setup.sh    # 建立 cache、logs 目錄（可選）
./scripts/start.sh    # 啟動 BIND 容器
./scripts/test-dns.sh # 查詢 example.com 與 localhost
./scripts/stop.sh     # 停止並移除容器
```

第一次啟動會先 build 映像，時間較久屬正常。

## 查詢方式

```bash
# 使用本機 BIND（127.0.0.1:53）
dig @127.0.0.1 example.com
dig @127.0.0.1 www.example.com
nslookup example.com 127.0.0.1
```

## 設定 macOS 使用本機 BIND DNS

### 快速設定

```bash
cd bind-dns-local/scripts
sudo bash ./setup-macos-dns.sh
```

腳本會自動：
- ✅ 偵測主要網路介面
- ✅ 設定 DNS 為 127.0.0.1
- ✅ 清除 DNS 快取
- ✅ 測試 DNS 解析

### 手動設定

```bash
# 設定 Wi-Fi 使用本機 BIND
sudo networksetup -setdnsservers Wi-Fi 127.0.0.1

# 清除 DNS 快取
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

**詳細說明**: 參考 `scripts/DNS設定指南.md`

## 自訂 Zone

1. 在 `config/named.conf.local` 新增 zone 區塊（參考 example.com）。
2. 在 `config/zones/` 新增對應 zone 檔（如 `db.mydomain.com`）。
3. 重載設定：`docker exec bind-dns-local rndc reload` 或重啟容器。

## 日誌與快取路徑

- **快取**：專案內 `cache/`（對應容器 `/var/cache/bind`）。
- **日誌**：專案內 `logs/`（對應容器 `/var/log/bind`），需容器有寫入權限；若未掛載則可改為輸出到 stdout。

## 改用本機 53 埠（可選）

若本機 53 已被佔用，可在 `docker-compose.yml` 將 `53:53` 改為例如 `5353:53` 或 `40053:53`，查詢時加上 `-p 5353` 或 `-p 40053`。

## 檔案結構

```
bind-dns-local/
├── README.md           # 本說明
├── docker-compose.yml  # BIND 服務與掛載
├── config/             # BIND 設定與內建 zone
│   ├── named.conf
│   ├── named.conf.local
│   ├── db.root
│   ├── db.local
│   ├── db.127, db.0, db.255, db.ip6.arpa
│   └── zones/          # 自訂 zone 檔
│       └── db.example.com
├── cache/              # 快取目錄（容器寫入）
├── logs/               # 日誌目錄（可選）
└── scripts/
    ├── setup.sh
    ├── start.sh
    ├── stop.sh
    ├── test-dns.sh
    ├── check-network.sh
    ├── deploy-ec2-websites.sh  # AWS EC2 自動部署腳本
    ├── dns-failover-test.sh    # DNS Failover 測試（整合自 Website/dns_test_pro.sh）
    ├── quick-failover-test.sh  # 快速測試腳本
    ├── EC2-部署指南.md         # EC2 部署詳細指南
    ├── 快速部署指南.md          # 快速部署說明
    └── README-DNS-Failover.md  # DNS Failover 測試說明
```

## AWS EC2 網站部署

### 快速部署兩台 EC2

使用自動部署腳本快速部署兩台 EC2，分別顯示不同的內容：

```bash
cd bind-dns-local/scripts
bash ./deploy-ec2-websites.sh
```

腳本會自動：
- ✅ 檢查並建立 Key Pair（如果不存在）
- ✅ 檢查並建立 Security Group（如果不存在）
- ✅ 自動選擇最新的 Amazon Linux 2 AMI
- ✅ 啟動兩台 EC2 實例並自動部署網站
- ✅ 顯示實例資訊和 IP

**詳細說明**: 參考 `scripts/快速部署指南.md`

## DNS Failover 測試

本專案整合了進階的 DNS failover 測試功能，可模擬 AWS/Google NS 異常場景。

### 使用場景

1. **EC2 部署**: 在 AWS 上部署兩台 EC2，分別顯示不同內容
   - EC2-1 (AWS): 顯示 "我是 AWS 3.3.3.3"
   - EC2-2 (Google): 顯示 "我是 Google 2.2.2.2"
2. **DNS 配置**: 域名同時配置 AWS Route53 和 Google Cloud DNS 作為 NS
3. **Failover 測試**: 使用本機防火牆阻擋特定 DNS 服務商，觀察系統切換行為

### 快速開始

```bash
# 1. 部署 EC2（參考 scripts/EC2-部署指南.md）
# 2. 配置 DNS（AWS Route53 + Google Cloud DNS）
# 3. 執行 failover 測試
cd bind-dns-local/scripts
sudo bash ./dns-failover-test.sh [域名] [AWS_EC2_IP] [Google_EC2_IP]

# 範例
sudo bash ./dns-failover-test.sh www.example.com 3.3.3.3 2.2.2.2
```

### 測試流程

腳本會執行以下測試階段：

1. **基準測試**: 無阻擋，確認域名可正常解析
2. **阻擋 AWS NS**: 只放行 Google NS，應解析到 Google EC2
3. **阻擋 Google NS**: 只放行 AWS NS，應解析到 AWS EC2
4. **全黑測試**: 阻擋所有 DNS，應無法解析
5. **切換測試**: 多次切換 NS，觀察系統反應時間

### 詳細說明

- **部署指南**: 參考 `scripts/EC2-部署指南.md`
- **測試腳本**: `scripts/dns-failover-test.sh`
- **日誌位置**: 
  - 主日誌: `/tmp/dns_failover_test_YYYYMMDD_HHMMSS.log`
  - Debug: `/tmp/dns_failover_debug.log`
  - 錯誤: `/tmp/dns_failover_errors.log`

### 注意事項

- ⚠️ 需要 `sudo` 權限（用於修改防火牆規則）
- ⚠️ 僅支援 macOS（使用 PF 防火牆）
- ⚠️ 測試完成後會自動還原防火牆規則
