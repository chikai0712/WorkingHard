# 🚀 DNS HA 模擬器 - 快速測試指南

## 第一步：啟動環境

### 方法 1：使用快速啟動腳本（推薦）

```bash
cd /Users/ckchiu/Desktop/Project/DNS-HA-Simulator
./scripts/quick-start.sh
```

### 方法 2：手動啟動

```bash
cd /Users/ckchiu/Desktop/Project/DNS-HA-Simulator

# 啟動所有服務
docker-compose up -d

# 等待服務就緒（約 15 秒）
sleep 15

# 檢查容器狀態
docker-compose ps
```

**預期結果**：所有容器應該顯示為 "Up" 狀態

---

## 第二步：開啟觀察視窗

### 視窗 A：Controller 監控（後台控制器）

開啟**第一個終端機視窗**：

```bash
docker logs -f dns-controller
```

**你應該看到：**
```
[INFO] DNS HA Controller Started
[SUCCESS] Main Service OK (172.20.0.10)
[SUCCESS] Main Service OK (172.20.0.10)
...
```

### 視窗 B：Client 測試（玩家端）

開啟**第二個終端機視窗**：

```bash
docker logs -f dns-client
```

**你應該看到：**
```
[CLIENT] ✅ Name: Main-Server-OK <--- [時間]
[CLIENT] ✅ Name: Main-Server-OK <--- [時間]
...
```

---

## 第三步：執行故障測試

開啟**第三個終端機視窗**，執行故障模擬：

```bash
# 停止主服務（模擬主機房斷線）
docker stop service-main
```

### 觀察結果

#### 視窗 A (Controller) 會顯示：
```
[WARN] Main Service FAILED (172.20.0.10) - Failure count: 1
[WARN] Main Service FAILED (172.20.0.10) - Failure count: 2
[WARN] Main Service FAILED (172.20.0.10) - Failure count: 3
[ALERT] FAILOVER TRIGGERED - Switching to Backup
[SUCCESS] DNS record updated: app.example.com -> 172.20.0.20
```

#### 視窗 B (Client) 會顯示：
```
[CLIENT] ❌ Connection Failed to 172.20.0.10
[CLIENT] DNS Resolution: app.example.com -> 172.20.0.20
[CLIENT] ✅ Name: Backup-Server-Active <--- [時間]
```

**✅ 成功標誌**：Client 自動恢復連線，顯示 "Backup-Server-Active"

---

## 第四步：恢復測試

在**第三個終端機視窗**執行：

```bash
# 恢復主服務
docker start service-main
```

### 觀察自動回切

#### 視窗 A (Controller) 會顯示：
```
[SUCCESS] Main Service OK (172.20.0.10)
[ALERT] RECOVERY DETECTED - Switching to Main
[SUCCESS] DNS record updated: app.example.com -> 172.20.0.10
```

#### 視窗 B (Client) 會顯示：
```
[CLIENT] DNS Resolution: app.example.com -> 172.20.0.10
[CLIENT] ✅ Name: Main-Server-OK <--- [時間]
```

**✅ 成功標誌**：Client 自動切換回主服務

---

## 快速驗證命令

### 檢查 DNS 解析

```bash
# 從 Client 容器測試 DNS
docker exec dns-client dig @172.20.0.101 app.example.com +short

# 預期輸出：172.20.0.10 或 172.20.0.20（取決於當前狀態）
```

### 檢查服務狀態

```bash
# 查看所有容器狀態
docker-compose ps

# 查看特定容器日誌
docker logs dns-controller --tail 20
docker logs dns-client --tail 20
```

### 手動測試 HTTP 服務

```bash
# 測試主服務
docker exec dns-client wget -qO- http://172.20.0.10/

# 測試備援服務
docker exec dns-client wget -qO- http://172.20.0.20/
```

---

## 常見問題

### Q: 容器無法啟動？

```bash
# 檢查 Docker 是否運行
docker info

# 查看錯誤日誌
docker-compose logs

# 重新啟動
docker-compose restart
```

### Q: DNS 解析失敗？

```bash
# 檢查 DNS 容器
docker logs dns-secondary

# 手動測試
docker exec dns-client dig @172.20.0.101 app.example.com
```

### Q: 看不到自動切換？

```bash
# 確認故障閾值已達到（需要連續 3 次失敗）
# 等待約 15 秒（3 次檢查 × 5 秒間隔）

# 檢查 Controller 日誌
docker logs dns-controller --tail 50
```

---

## 清理環境

測試完成後，停止所有服務：

```bash
# 停止所有容器
docker-compose down

# 完全清理（包括 volumes）
docker-compose down -v
```

---

## 📊 測試檢查清單

- [ ] 所有容器成功啟動
- [ ] Controller 顯示 "Main Service OK"
- [ ] Client 顯示 "Main-Server-OK"
- [ ] 停止主服務後，Controller 偵測到故障
- [ ] Controller 自動切換到備援服務
- [ ] Client 自動恢復連線（顯示 "Backup-Server-Active"）
- [ ] 恢復主服務後，Controller 自動回切
- [ ] Client 自動切換回主服務

---

**測試時間**：約 5-10 分鐘  
**難度**：⭐ 簡單

