# DNS 高可用性自動備援模擬器

一個在 macOS 上使用 Docker 環境模擬 Multi-Vendor DNS 架構的完整解決方案。演示當 Primary Service 發生故障時，Controller 如何自動偵測並透過 API 修改 Secondary DNS 的紀錄，將流量導向 Backup Service。

## 📋 專案概述

本專案模擬了一個真實的 DNS 高可用性場景：
- **Primary DNS** 完全故障（模擬 Cloudflare 中斷）
- **Secondary DNS** 作為備援（模擬 Google DNS）
- **Controller** 自動監控並執行故障轉移
- **Client** 持續測試連線，觀察切換過程

## 🏗️ 架構圖

```
Internet/Client
    ↓
Secondary DNS (172.20.0.101) ← Controller (172.20.0.5) 監控
    ↓                              ↓
Primary DNS (172.20.0.100) [故障]   Main Service (172.20.0.10)
    ↓                              Backup Service (172.20.0.20)
```

## 🚀 快速開始

### 前置需求

- macOS (已測試)
- Docker Desktop for Mac
- Docker Compose v2.0+

### 安裝步驟

1. **克隆或下載專案**
   ```bash
   cd /Users/ckchiu/Desktop/Project/DNS-HA-Simulator
   ```

2. **設定執行權限**
   ```bash
   chmod +x scripts/*.sh
   ```

3. **啟動所有服務**
   ```bash
   docker-compose up -d
   ```

4. **等待服務就緒（約 15 秒）**
   ```bash
   sleep 15
   ```

## 📖 使用指南

### 基本操作流程

#### 1. 開啟觀察視窗

**視窗 A - Controller 監控：**
```bash
docker logs -f dns-controller
```

**視窗 B - Client 測試：**
```bash
docker logs -f dns-client
```

#### 2. 模擬故障

在**第三個終端機視窗**執行：
```bash
docker stop service-main
```

#### 3. 觀察自動切換

- **視窗 A** 會顯示故障偵測和切換過程
- **視窗 B** 會顯示 Client 的連線狀態變化

#### 4. 恢復服務

```bash
docker start service-main
```

系統會自動切換回主服務。

### 在 macOS 主機上測試 DNS（可選）

如果您想在 macOS 主機上直接測試 DNS 解析（使用標準 53 端口），需要設置 port forward：

#### 快速設置（推薦）

```bash
# 使用簡化腳本（只需輸入一次密碼）
./scripts/fix-dns-port-easy.sh

# 或使用快速修復腳本
./快速修復.sh
```

#### 手動設置

```bash
# 1. 停止 macOS DNS 服務
sudo launchctl unload -w /System/Library/LaunchDaemons/com.apple.mDNSResponder.plist

# 2. 啟動 port forward
sudo ./scripts/setup-dns-forward.sh start

# 3. 設定 macOS DNS 為 127.0.0.1
# 系統設定 > 網路 > Wi-Fi > 詳細資訊 > DNS > 新增 127.0.0.1

# 4. 清空 DNS cache
sudo killall -HUP mDNSResponder

# 5. 測試
dig app.example.com
```

#### 恢復 macOS DNS

```bash
# 停止 port forward
sudo ./scripts/setup-dns-forward.sh stop

# 恢復 macOS DNS 服務
sudo launchctl load -w /System/Library/LaunchDaemons/com.apple.mDNSResponder.plist
```

**注意**：
- 設置 port forward 需要 sudo 權限（需要輸入密碼）
- 詳細說明請參考 [使用說明-密碼處理.md](./使用說明-密碼處理.md)
- 如果不想處理密碼，可以使用備用方案：直接測試 5300 端口或 Docker 容器內測試

### 完整測試流程

詳細的執行步驟請參考 [DNS_HA_Plan_Spec.md](./DNS_HA_Plan_Spec.md)

## 📁 專案結構

```
DNS-HA-Simulator/
├── README.md                          # 本文件
├── DNS_HA_Plan_Spec.md                # 完整計畫書
├── 快速修復.sh                        # 一鍵修復 DNS port forward
├── docker-compose.yml                 # Docker Compose 配置
├── scripts/
│   ├── monitor.sh                     # Controller 監控腳本
│   ├── client-test.sh                 # Client 測試腳本
│   ├── dns-server.py                  # 自定義 DNS 服務器
│   ├── fix-dns-port.sh                # DNS port forward 修復腳本
│   ├── fix-dns-port-easy.sh           # 簡化版修復腳本（自動處理 sudo）
│   └── setup-dns-forward.sh           # Port forward 設定腳本
├── services/
│   ├── main/
│   │   └── index.html                # 主服務回應頁面
│   └── backup/
│       └── index.html                 # 備援服務回應頁面
└── dns_config/
    ├── primary/
    │   └── named.conf                 # Primary DNS 配置（故障）
    └── secondary/
        ├── named.conf                 # Secondary DNS 配置
        └── zones/
            └── app.example.com.zone    # DNS Zone 文件
```

## 🔧 配置說明

### 環境變數

可以在 `docker-compose.yml` 中調整以下參數：

- `CHECK_INTERVAL`: Controller 檢查間隔（預設 5 秒）
- `MAIN_SERVICE_IP`: 主服務 IP（預設 172.20.0.10）
- `BACKUP_SERVICE_IP`: 備援服務 IP（預設 172.20.0.20）
- `DNS_SECONDARY_IP`: Secondary DNS IP（預設 172.20.0.101）

### DNS 配置

DNS Zone 文件位於：
```
dns_config/secondary/zones/app.example.com.zone
```

Controller 會自動修改此文件並重新載入 DNS。

## 🧪 測試場景

### 場景 1：主服務故障

1. 啟動所有服務
2. 觀察正常運作
3. 停止主服務：`docker stop service-main`
4. 觀察自動切換到備援服務
5. 恢復主服務：`docker start service-main`
6. 觀察自動切換回主服務

### 場景 2：DNS 服務器故障

1. 停止 Secondary DNS：`docker stop dns-secondary`
2. 觀察 Client 無法解析 DNS
3. 恢復 DNS：`docker start dns-secondary`
4. 觀察服務恢復

### 場景 3：同時故障

1. 停止主服務和備援服務
2. 觀察 Controller 的錯誤處理
3. 恢復服務
4. 觀察自動恢復

## 📊 預期輸出

### Controller 正常運作
```
[INFO] DNS HA Controller Started
[INFO] Main Service IP: 172.20.0.10
[SUCCESS] Main Service OK (172.20.0.10)
```

### Controller 故障偵測
```
[WARN] Main Service FAILED (172.20.0.10) - Failure count: 1
[ALERT] FAILOVER TRIGGERED - Switching to Backup
[SUCCESS] DNS record updated: app.example.com -> 172.20.0.20
```

### Client 正常連線
```
[CLIENT] ✅ Name: Main-Server-OK <--- [14:30:25]
[CLIENT] ✅ Name: Main-Server-OK <--- [14:30:27]
```

### Client 故障恢復
```
[CLIENT] ❌ Connection Failed to 172.20.0.10
[CLIENT] DNS Resolution: app.example.com -> 172.20.0.20
[CLIENT] ✅ Name: Backup-Server-Active <--- [14:30:35]
```

## 🐛 故障排除

### 問題：容器無法啟動

```bash
# 檢查 Docker 狀態
docker ps -a

# 查看容器日誌
docker logs <container-name>

# 重新啟動
docker-compose restart
```

### 問題：DNS 解析失敗

```bash
# 檢查 DNS 容器
docker logs dns-secondary

# 手動測試 DNS
docker exec dns-client dig @172.20.0.101 app.example.com
```

### 問題：Controller 無法更新 DNS

```bash
# 檢查權限
docker exec dns-controller ls -la /zones/

# 檢查 zone 文件
docker exec dns-controller cat /zones/app.example.com.zone
```

## 🔒 安全注意事項

- 本模擬環境僅用於測試，不應在生產環境使用
- 所有容器運行在隔離的 Docker 網路中
- DNS 配置允許所有查詢，實際環境應限制訪問
- 模擬的 API 調用僅為演示目的

## 📈 擴展建議

1. **多域名支援**：擴展支援多個域名
2. **真實 API 整合**：替換模擬 API 為真實的 DNS 提供商 API
3. **監控儀表板**：整合 Prometheus 和 Grafana
4. **自動回切優化**：實現更智能的回切邏輯
5. **健康檢查增強**：加入更複雜的健康檢查機制

## 📝 版本歷史

- **v1.0** (2024) - 初始版本
  - 基本故障偵測與切換
  - DNS 自動更新
  - Client 持續測試

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

## 📄 授權

本專案僅供學習和測試使用。

---

**專案狀態**：✅ 可用  
**最後更新**：2024

