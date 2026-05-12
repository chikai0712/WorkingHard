# DNS Port Forward 設定指南

## 問題說明

Docker 容器內的 DNS 服務器（`dns-secondary`）運行在內部網路 `172.20.0.101:53`，你的 macOS 無法直接訪問。雖然 Docker 已經將端口映射到宿主機的 `5300` 端口，但 macOS 的 DNS 設定只能使用標準的 `53` 端口。

## 解決方案

有兩種方法可以讓 macOS 使用 Docker 內的 DNS 服務器：

### 方法 1：使用 socat 做 Port Forward（推薦）

#### 步驟 1：安裝 socat

```bash
brew install socat
```

#### 步驟 2：暫時停止 macOS 的 mDNSResponder（釋放 53 端口）

```bash
sudo launchctl unload -w /System/Library/LaunchDaemons/com.apple.mDNSResponder.plist
```

> **注意**：這會暫時停止 macOS 的 DNS 服務，測試完成後需要恢復。

#### 步驟 3：啟動 Port Forward

```bash
cd /Users/ckchiu/Desktop/Project/DNS-HA-Simulator
sudo ./scripts/setup-dns-forward.sh start
```

這會啟動 socat，將 `127.0.0.1:53` 的查詢轉發到 `127.0.0.1:5300`。

#### 步驟 4：設定 macOS DNS

1. 開啟 **系統設定 > 網路 > Wi-Fi > 詳細資訊 > DNS**
2. 移除所有 DNS 伺服器
3. 新增：`127.0.0.1`
4. 按「好」→「套用」

#### 步驟 5：測試

```bash
# 清空 DNS cache
sudo killall -HUP mDNSResponder

# 測試 DNS 解析
dig app.example.com
```

#### 步驟 6：測試完成後恢復

```bash
# 停止 port forward
sudo ./scripts/setup-dns-forward.sh stop

# 恢復 macOS DNS 服務
sudo launchctl load -w /System/Library/LaunchDaemons/com.apple.mDNSResponder.plist

# 恢復 macOS DNS 設定（改回原本的 DNS 伺服器）
```

---

### 方法 2：修改 Docker 配置直接監聽 53 端口

#### 步驟 1：修改 docker-compose.yml

```bash
cd /Users/ckchiu/Desktop/Project/DNS-HA-Simulator
sudo ./scripts/setup-dns-forward.sh docker
```

這會自動修改 `docker-compose.yml`，將端口映射從 `5300:53` 改為 `53:53`。

#### 步驟 2：停止 macOS DNS 服務

```bash
sudo launchctl unload -w /System/Library/LaunchDaemons/com.apple.mDNSResponder.plist
```

#### 步驟 3：重啟 DNS 容器

```bash
docker-compose up -d dns-secondary
```

#### 步驟 4：設定 macOS DNS

同方法 1 的步驟 4。

---

## 完整測試流程

### 1. 準備環境

```bash
cd /Users/ckchiu/Desktop/Project/DNS-HA-Simulator

# 確保所有容器運行
docker-compose up -d

# 啟動 port forward（方法 1）
sudo ./scripts/setup-dns-forward.sh start

# 設定 macOS DNS 為 127.0.0.1
# （透過系統設定手動操作）
```

### 2. 開始抓包

在**另一個終端機視窗**執行：

```bash
# 獲取你的 Mac IP（Wi-Fi 介面）
MY_IP=$(ipconfig getifaddr en0)
echo "你的 Mac IP: $MY_IP"

# 開始抓包
sudo tcpdump -i any udp port 53 and host $MY_IP -w ~/dns_retry_test.pcap
```

### 3. 觸發 DNS 查詢

在**第三個終端機視窗**執行：

```bash
# 清空 DNS cache
sudo killall -HUP mDNSResponder

# 觸發查詢（這會觸發 macOS 的 retry 機制）
dig app.example.com

# 或模擬遊戲連線
while true; do
  dig app.example.com >/dev/null 2>&1
  sleep 5
done
```

### 4. 停止抓包

在抓包的終端機按 `Ctrl+C` 停止 tcpdump。

### 5. 分析結果

```bash
# 用 Wireshark 打開
open ~/dns_retry_test.pcap

# 或在終端機分析
tcpdump -r ~/dns_retry_test.pcap -n
```

### 6. 清理環境

```bash
# 停止 port forward
sudo ./scripts/setup-dns-forward.sh stop

# 恢復 macOS DNS 服務
sudo launchctl load -w /System/Library/LaunchDaemons/com.apple.mDNSResponder.plist

# 恢復 macOS DNS 設定
```

---

## 注意事項

1. **53 端口需要 root 權限**：所有操作都需要使用 `sudo`
2. **會影響系統 DNS**：測試期間 macOS 的 DNS 解析會使用你的測試 DNS
3. **測試完成後記得恢復**：避免影響正常上網
4. **mDNSResponder**：停止後可能影響 AirDrop、Bonjour 等功能，測試完成後記得恢復

---

## 故障排除

### 問題：端口 53 被占用

```bash
# 檢查誰在使用 53 端口
sudo lsof -i :53

# 停止 mDNSResponder
sudo launchctl unload -w /System/Library/LaunchDaemons/com.apple.mDNSResponder.plist
```

### 問題：socat 未安裝

```bash
# 安裝 Homebrew（如果沒有）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安裝 socat
brew install socat
```

### 問題：DNS 查詢失敗

```bash
# 檢查 Docker DNS 是否運行
docker-compose ps dns-secondary

# 檢查 port forward 是否運行
ps aux | grep socat

# 測試直接連 5300 端口
dig @127.0.0.1 -p 5300 app.example.com
```

---

## 快速參考

```bash
# 啟動 port forward
sudo ./scripts/setup-dns-forward.sh start

# 停止 port forward
sudo ./scripts/setup-dns-forward.sh stop

# 檢查狀態
ps aux | grep socat
sudo lsof -i :53
```

---

**版本**：v1.0  
**最後更新**：2025-12-02

