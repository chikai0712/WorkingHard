# DNS HA 模擬器 - 完整執行指南

## 📋 目錄

1. [快速開始](#快速開始)
2. [詳細執行步驟](#詳細執行步驟)
3. [觀察與驗證](#觀察與驗證)
4. [故障模擬場景](#故障模擬場景)
5. [故障排除](#故障排除)

## 🚀 快速開始

### 一鍵啟動

```bash
cd /Users/ckchiu/Desktop/Project/DNS-HA-Simulator
chmod +x scripts/*.sh
./scripts/quick-start.sh
```

### 手動啟動

```bash
# 1. 進入專案目錄
cd /Users/ckchiu/Desktop/Project/DNS-HA-Simulator

# 2. 設定權限
chmod +x scripts/*.sh

# 3. 啟動所有服務
docker-compose up -d

# 4. 等待服務就緒（約 15 秒）
sleep 15

# 5. 檢查容器狀態
docker-compose ps
```

## 📖 詳細執行步驟

### 第一階段：啟動環境

#### 步驟 1：確認環境

```bash
# 檢查 Docker
docker --version
docker-compose --version

# 確認 Docker 運行中
docker info
```

#### 步驟 2：啟動服務

```bash
# 啟動所有容器
docker-compose up -d

# 查看啟動日誌
docker-compose logs
```

#### 步驟 3：驗證服務狀態

```bash
# 檢查所有容器狀態
docker-compose ps

# 預期輸出應該顯示所有容器都是 "Up" 狀態
```

### 第二階段：開啟觀察視窗

**重要**：需要開啟**兩個終端機視窗**同時觀察。

#### 視窗 A：Controller 監控

```bash
docker logs -f dns-controller
```

**預期輸出：**
```
[INFO] DNS HA Controller Started
[INFO] Main Service IP: 172.20.0.10
[INFO] Backup Service IP: 172.20.0.20
[INFO] DNS Secondary IP: 172.20.0.101
[INFO] Check Interval: 5 seconds
[INFO] Current Target: main
[INFO] Initializing DNS to point to Main Service...
[SUCCESS] DNS record updated: app.example.com -> 172.20.0.10
[SUCCESS] DNS zone file updated, server will auto-reload
[SUCCESS] Main Service OK (172.20.0.10)
[SUCCESS] Main Service OK (172.20.0.10)
```

#### 視窗 B：Client 測試

```bash
docker logs -f dns-client
```

**預期輸出：**
```
[CLIENT] DNS Client Started
[CLIENT] Domain: app.example.com
[CLIENT] DNS Server: 172.20.0.101
[CLIENT] DNS Resolution: app.example.com -> 172.20.0.10
[CLIENT] ✅ Name: Main-Server-OK <--- [14:30:25]
[CLIENT] ✅ Name: Main-Server-OK <--- [14:30:27]
[CLIENT] ✅ Name: Main-Server-OK <--- [14:30:29]
```

### 第三階段：模擬故障

開啟**第三個終端機視窗**執行故障模擬：

```bash
# 停止主服務
docker stop service-main
```

### 第四階段：觀察自動切換

#### 視窗 A (Controller) 會顯示：

```
[WARN] Main Service FAILED (172.20.0.10) - Failure count: 1
[WARN] Main Service FAILED (172.20.0.10) - Failure count: 2
[WARN] Main Service FAILED (172.20.0.10) - Failure count: 3
[ALERT] ==========================================
[ALERT] FAILOVER TRIGGERED - Switching to Backup
[ALERT] ==========================================
[INFO] Simulating API call to update DNS...
[INFO]   API Endpoint: https://api.dns-provider.com/v1/zones/app.example.com/records
[INFO]   Method: PATCH
[INFO]   Payload: {"type":"A","name":"app","content":"172.20.0.20"}
[SUCCESS] API call completed (simulated)
[INFO] Updating DNS record for app.example.com to 172.20.0.20 (backup)...
[SUCCESS] DNS record updated: app.example.com -> 172.20.0.20
[SUCCESS] DNS zone file updated, server will auto-reload
[ALERT] Failover completed: app.example.com -> 172.20.0.20
```

#### 視窗 B (Client) 會顯示：

```
[CLIENT] ❌ Connection Failed to 172.20.0.10 <--- [14:30:35]
[CLIENT] ❌ Connection Failed to 172.20.0.10 <--- [14:30:37]
[CLIENT] DNS Resolution: app.example.com -> 172.20.0.20
[CLIENT] ✅ Name: Backup-Server-Active <--- [14:30:39]
[CLIENT] ✅ Name: Backup-Server-Active <--- [14:30:41]
```

### 第五階段：恢復服務

在**第三個終端機視窗**執行：

```bash
# 恢復主服務
docker start service-main
```

#### 觀察自動回切

**視窗 A (Controller)：**
```
[SUCCESS] Main Service OK (172.20.0.10)
[ALERT] ==========================================
[ALERT] RECOVERY DETECTED - Switching to Main
[ALERT] ==========================================
[INFO] Simulating API call to update DNS...
[SUCCESS] DNS record updated: app.example.com -> 172.20.0.10
[ALERT] Recovery completed: app.example.com -> 172.20.0.10
```

**視窗 B (Client)：**
```
[CLIENT] DNS Resolution: app.example.com -> 172.20.0.10
[CLIENT] ✅ Name: Main-Server-OK <--- [14:31:15]
```

## 🧪 故障模擬場景

### 場景 1：主服務故障（標準流程）

1. **啟動所有服務**
   ```bash
   docker-compose up -d
   ```

2. **觀察正常運作**
   - 確認 Controller 顯示 "Main Service OK"
   - 確認 Client 顯示 "Main-Server-OK"

3. **模擬故障**
   ```bash
   docker stop service-main
   ```

4. **觀察切換**
   - Controller 偵測故障並切換
   - Client 自動恢復連線

5. **恢復服務**
   ```bash
   docker start service-main
   ```

6. **觀察回切**
   - Controller 自動切換回主服務
   - Client 連線恢復正常

### 場景 2：DNS 服務器故障

```bash
# 停止 Secondary DNS
docker stop dns-secondary

# 觀察 Client 無法解析 DNS
# 預期：Client 顯示 "DNS Resolution FAILED"

# 恢復 DNS
docker start dns-secondary

# 觀察服務恢復
```

### 場景 3：同時故障多個服務

```bash
# 停止主服務和備援服務
docker stop service-main service-backup

# 觀察 Controller 的錯誤處理
# 預期：顯示 "Backup service also failed!"

# 恢復服務
docker start service-main service-backup
```

### 場景 4：網路隔離測試

```bash
# 隔離主服務網路
docker network disconnect dns-ha-network service-main

# 觀察故障偵測和切換

# 恢復網路
docker network connect dns-ha-network service-main
```

## 🔍 觀察與驗證

### 檢查 DNS 記錄

```bash
# 從 Client 容器測試 DNS
docker exec dns-client dig @172.20.0.101 app.example.com

# 預期輸出應該顯示當前的 IP 地址
```

### 檢查服務狀態

```bash
# 檢查所有容器狀態
docker-compose ps

# 檢查特定容器日誌
docker logs dns-controller --tail 50
docker logs dns-client --tail 50
docker logs dns-secondary --tail 50
```

### 檢查 Zone 文件

```bash
# 查看當前的 DNS 記錄
cat dns_config/secondary/zones/app.example.com.zone

# 或從容器內查看
docker exec dns-controller cat /zones/app.example.com.zone
```

### 手動測試 HTTP 服務

```bash
# 測試主服務
docker exec dns-client wget -qO- http://172.20.0.10/

# 測試備援服務
docker exec dns-client wget -qO- http://172.20.0.20/
```

## 🐛 故障排除

### 問題 1：容器無法啟動

**症狀**：`docker-compose ps` 顯示容器狀態為 "Exited"

**解決方法**：
```bash
# 查看容器日誌
docker logs <container-name>

# 檢查端口衝突
netstat -an | grep 5300

# 重新啟動
docker-compose restart
```

### 問題 2：DNS 解析失敗

**症狀**：Client 顯示 "DNS Resolution FAILED"

**解決方法**：
```bash
# 檢查 DNS 容器狀態
docker logs dns-secondary

# 手動測試 DNS
docker exec dns-client dig @172.20.0.101 app.example.com

# 檢查 zone 文件
docker exec dns-controller cat /zones/app.example.com.zone

# 重啟 DNS 容器
docker-compose restart dns-secondary
```

### 問題 3：Controller 無法更新 DNS

**症狀**：Controller 顯示更新失敗

**解決方法**：
```bash
# 檢查 zone 文件權限
docker exec dns-controller ls -la /zones/

# 檢查文件內容
docker exec dns-controller cat /zones/app.example.com.zone

# 手動測試更新
docker exec dns-controller sh -c 'echo "test" >> /zones/test.txt'
```

### 問題 4：服務無法連線

**症狀**：Client 顯示 "Connection Failed"

**解決方法**：
```bash
# 檢查服務容器狀態
docker ps -a | grep service

# 測試網路連通性
docker exec dns-client ping -c 3 172.20.0.10
docker exec dns-client ping -c 3 172.20.0.20

# 檢查 HTTP 服務
docker exec dns-client wget -qO- http://172.20.0.10/
```

### 問題 5：自動切換不工作

**症狀**：主服務故障但未自動切換

**解決方法**：
```bash
# 檢查 Controller 日誌
docker logs dns-controller --tail 100

# 確認故障閾值設定
# 預設為連續 3 次失敗，檢查是否達到

# 手動測試服務檢查
docker exec dns-controller wget --timeout=2 --tries=1 --spider http://172.20.0.10/
```

## 🧹 清理環境

### 停止所有服務

```bash
docker-compose down
```

### 完全清理（包括 volumes）

```bash
docker-compose down -v
```

### 清理 Docker 資源

```bash
# 清理未使用的容器、網路、鏡像
docker system prune -a

# 僅清理未使用的容器
docker container prune
```

## 📊 性能監控

### 查看資源使用

```bash
# 查看容器資源使用
docker stats

# 查看特定容器
docker stats dns-controller dns-client
```

### 查看網路流量

```bash
# 查看網路連接
docker network inspect dns-ha-network

# 查看容器網路統計
docker exec dns-client netstat -an
```

## 📝 注意事項

1. **首次啟動**：需要等待約 15-20 秒讓所有服務完全啟動
2. **DNS TTL**：設為 300 秒，實際環境可能需要調整
3. **故障閾值**：預設為連續 3 次失敗，可在 `monitor.sh` 中調整
4. **檢查間隔**：Controller 每 5 秒檢查一次，可在環境變數中調整
5. **Zone 文件**：DNS 服務器每 2 秒自動重新載入 zone 文件

---

**版本**：v1.0  
**最後更新**：2024

