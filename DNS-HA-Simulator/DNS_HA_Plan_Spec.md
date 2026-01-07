# DNS 高可用性 (HA) 自動備援模擬計畫書

## 1. 專案目標 (Objective)

在 macOS 上使用 Docker 環境，模擬一個真實的 Multi-Vendor DNS 架構。演示當 Primary Service (主要服務) 發生故障時，Controller (控制器) 如何自動偵測並透過模擬的 API 修改 Secondary DNS (備援 DNS) 的紀錄，將流量導向 Backup Service (備援服務)，同時觀察對玩家端 (Client) 的影響。

## 2. 模擬架構 (Architecture)

本模擬包含 6 個 Docker 容器，組成一個獨立的內部網路：

| 角色 (Role) | 容器名稱 | 模擬對象 | IP 位址 (Fixed) | 功能描述 |
|------------|---------|---------|----------------|----------|
| **Primary Service** | `service-main` | 主機房 Web Server | `172.20.0.10` | 正常運作時的目標伺服器 (回應: "Main Server OK") |
| **Backup Service** | `service-backup` | 備援機房 Web Server | `172.20.0.20` | 故障時的接手伺服器 (回應: "Backup Server Active") |
| **Primary DNS** | `dns-primary` | Cloudflare (模擬) | `172.20.0.100` | 模擬完全故障的 DNS，無法提供服務 |
| **Secondary DNS** | `dns-secondary` | Google DNS (模擬) | `172.20.0.101` | 備援 DNS 解析器。接受 Controller 的指令修改 A 紀錄 |
| **Controller** | `dns-controller` | 自動化腳本主機 | `172.20.0.5` | 執行 `monitor.sh`。負責 Ping 偵測與 API 切換 |
| **Client** | `dns-client` | 玩家端電腦 | `172.20.0.50` | 模擬玩家持續連線。強制使用 Secondary DNS 進行解析 |

### 網路拓撲

```
┌─────────────────────────────────────────────────────────┐
│              Docker Network: 172.20.0.0/24              │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐      ┌──────────────┐                 │
│  │ service-main │      │service-backup│                 │
│  │  172.20.0.10 │      │  172.20.0.20 │                 │
│  └──────┬───────┘      └──────┬───────┘                 │
│         │                     │                          │
│         └──────────┬──────────┘                         │
│                    │                                      │
│  ┌────────────────┴────────────────┐                   │
│  │      dns-controller              │                   │
│  │        172.20.0.5                │                   │
│  │    (monitor.sh)                  │                   │
│  └────────────────┬─────────────────┘                   │
│                   │                                      │
│         ┌─────────┴─────────┐                           │
│         │                   │                           │
│  ┌──────▼──────┐    ┌───────▼──────┐                   │
│  │dns-primary  │    │dns-secondary │                   │
│  │172.20.0.100 │    │ 172.20.0.101 │                   │
│  │  (故障)      │    │  (可修改)     │                   │
│  └─────────────┘    └───────┬───────┘                   │
│                              │                            │
│                       ┌──────▼──────┐                    │
│                       │ dns-client  │                    │
│                       │ 172.20.0.50 │                    │
│                       │ (玩家端)     │                    │
│                       └─────────────┘                    │
└─────────────────────────────────────────────────────────┘
```

## 3. 運作邏輯 (Logic Flow)

### 正常狀態 (Normal State)

1. Client 查詢 `app.example.com` → 得到 `172.20.0.10` → 連線成功 (回應 "Main Server OK")
2. Controller 每 5 秒檢查一次 Main Service
3. 所有服務正常運作

### 故障模擬 (Failure Simulation)

1. 使用者手動執行 `docker stop service-main`
2. Client 開始出現連線逾時或錯誤 (模擬玩家斷線)
3. Controller 偵測到 Main Service 無回應 (連續 3 次失敗)

### 自動切換 (Failover Action)

1. Controller 判斷 Main Service 離線
2. Controller 執行模擬 "API Call" (修改 dns-secondary 設定並重載)
3. `dns-secondary` 上的 `app.example.com` 紀錄變更指向 `172.20.0.20` (Backup)
4. DNS 區域重新載入完成

### 玩家端恢復 (Client Recovery)

1. Client 下一次請求查詢到新 IP `172.20.0.20`
2. Client 連線成功 (回應 "Backup Server Active")
3. 服務恢復正常運作

### 主服務恢復 (Main Service Recovery)

1. 使用者執行 `docker start service-main`
2. Controller 偵測到 Main Service 恢復
3. Controller 自動切換回 Main Service
4. DNS 記錄更新回 `172.20.0.10`
5. Client 自動切換回主服務

## 4. 執行步驟 (Execution Plan)

### 前置準備

1. **建立專案目錄**
   ```bash
   cd /Users/ckchiu/Desktop/Project
   mkdir -p DNS-HA-Simulator
   cd DNS-HA-Simulator
   ```

2. **確認 Docker 環境**
   ```bash
   docker --version
   docker-compose --version
   ```

3. **設定執行權限**
   ```bash
   chmod +x scripts/*.sh
   ```

### 第一階段：啟動環境

```bash
# 啟動所有容器
docker-compose up -d

# 檢查容器狀態
docker-compose ps

# 等待所有服務就緒（約 10-15 秒）
sleep 15
```

### 第二階段：開啟觀察視窗 (關鍵)

我們需要開啟**兩個終端機視窗**來觀察對比。

#### 視窗 A (後台控制器)：查看自動化切換邏輯

```bash
docker logs -f dns-controller
```

**預期輸出：**
```
[INFO] DNS HA Controller Started
[INFO] Main Service IP: 172.20.0.10
[INFO] Backup Service IP: 172.20.0.20
[SUCCESS] Main Service OK (172.20.0.10)
```

#### 視窗 B (前台玩家端)：查看玩家連線狀況

```bash
docker logs -f dns-client
```

**預期輸出：**
```
[CLIENT] DNS Resolution: app.example.com -> 172.20.0.10
[CLIENT] ✅ Name: Main-Server-OK <--- [14:30:25]
[CLIENT] ✅ Name: Main-Server-OK <--- [14:30:27]
```

### 第三階段：執行破壞

開啟**第三個終端機視窗**，模擬主機房斷線：

```bash
docker stop service-main
```

### 第四階段：觀察結果

#### 視窗 B (玩家端)：
- 會看到幾秒鐘的 `❌ Connection Failed`
- 然後自動恢復，回應變成了 `✅ Name: Backup-Server-Active <--- [時間]`

#### 視窗 A (控制器)：
- 顯示 `[WARN] Main Service FAILED`
- 顯示 `[ALERT] FAILOVER TRIGGERED - Switching to Backup`
- 顯示 `[SUCCESS] DNS record updated: app.example.com -> 172.20.0.20`

### 第五階段：恢復

啟動主服務：

```bash
docker start service-main
```

觀察兩個視窗，確認服務自動切換回 Main Server。

### 清理環境

```bash
# 停止所有容器
docker-compose down

# 完全清理（包括 volumes）
docker-compose down -v
```

## 5. 技術細節

### Controller 監控邏輯

- **檢查間隔**：每 5 秒檢查一次主服務
- **故障閾值**：連續 3 次失敗後觸發切換
- **DNS 更新**：使用 `sed` 修改 zone 文件，然後使用 `rndc reload` 重新載入
- **API 模擬**：模擬真實 DNS API 調用流程

### DNS 配置

- **Zone 文件**：`dns_config/secondary/zones/app.example.com.zone`
- **初始 A 記錄**：指向 `172.20.0.10` (Main Service)
- **切換後**：更新為 `172.20.0.20` (Backup Service)

### Client 測試邏輯

- **DNS 解析**：使用 `dig` 查詢 Secondary DNS
- **HTTP 測試**：使用 `wget` 測試 HTTP 連線
- **檢查間隔**：每 2 秒檢查一次
- **狀態顯示**：根據回應內容顯示服務類型

## 6. 故障排除

### 問題：DNS 解析失敗

```bash
# 檢查 DNS 容器狀態
docker logs dns-secondary

# 手動測試 DNS
docker exec dns-client dig @172.20.0.101 app.example.com
```

### 問題：Controller 無法更新 DNS

```bash
# 檢查 Controller 日誌
docker logs dns-controller

# 檢查 zone 文件權限
docker exec dns-controller ls -la /zones/
```

### 問題：服務無法連線

```bash
# 檢查服務容器狀態
docker ps -a

# 檢查網路連線
docker exec dns-client ping -c 3 172.20.0.10
docker exec dns-client ping -c 3 172.20.0.20
```

## 7. 擴展建議

1. **多區域支援**：擴展支援多個域名和區域
2. **健康檢查增強**：加入更複雜的健康檢查邏輯
3. **監控儀表板**：整合 Prometheus 和 Grafana
4. **真實 API 整合**：替換模擬 API 為真實的 Cloudflare/Google DNS API
5. **自動回切**：實現更智能的自動回切邏輯

## 8. 注意事項

- 本模擬使用固定 IP 地址，實際環境中應使用動態配置
- DNS TTL 設為 300 秒，實際環境可能需要調整
- 模擬的 API 調用僅為演示，實際環境需要真實的 API 憑證和端點
- 所有容器運行在隔離的 Docker 網路中，不會影響主機網路

---

**版本**：v1.0  
**最後更新**：2024  
**作者**：DNS HA Simulator Team

