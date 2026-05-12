# DNS Port Forward 問題修復指南

## 問題診斷

根據您的測試結果，發現以下問題：
1. **socat 顯示 "Address already in use"** - 53 端口被占用
2. **dig 查詢超時** - DNS 無法連接

## 根本原因

macOS 的 `mDNSResponder` 服務會自動重新啟動並占用 53 端口，導致我們的 port forward 無法正常工作。

## 解決方案

### 方法 1: 使用修復腳本（推薦）

```bash
cd /Users/ckchiu/Desktop/Project/DNS-HA-Simulator
sudo ./scripts/fix-dns-port.sh
```

這個腳本會：
1. 停止所有現有的 port forward
2. 強制停止 mDNSResponder
3. 確保 53 端口已釋放
4. 重新啟動 port forward
5. 驗證功能

### 方法 2: 手動修復步驟

如果腳本無法解決，請按以下步驟手動操作：

```bash
# 1. 停止現有的 port forward
sudo ./scripts/setup-dns-forward.sh stop

# 2. 強制停止 mDNSResponder
sudo launchctl unload -w /System/Library/LaunchDaemons/com.apple.mDNSResponder.plist
sudo killall mDNSResponder
sudo killall mDNSResponderHelper

# 3. 等待 3 秒確保端口釋放
sleep 3

# 4. 檢查 53 端口是否已釋放
sudo lsof -i :53 -sTCP:LISTEN

# 5. 如果仍有進程占用，強制殺掉
sudo lsof -i :53 -sTCP:LISTEN | awk 'NR>1 {print $2}' | xargs sudo kill -9

# 6. 重新啟動 port forward
sudo ./QUICK_SETUP.sh

# 7. 清空 DNS cache
sudo killall -HUP mDNSResponder

# 8. 測試
dig app.example.com
```

### 方法 3: 使用 dig 直接指定服務器（繞過系統 DNS）

如果 port forward 仍有問題，可以直接測試：

```bash
# 直接查詢 5300 端口（繞過 port forward）
dig @127.0.0.1 -p 5300 app.example.com

# 或直接查詢容器 IP（如果可達）
dig @172.20.0.101 app.example.com
```

## 驗證步驟

執行修復後，請驗證：

```bash
# 1. 檢查 port forward 進程
ps aux | grep socat | grep 53

# 2. 檢查 53 端口狀態
sudo lsof -i :53 -sTCP:LISTEN

# 3. 測試 DNS 查詢
dig app.example.com

# 4. 檢查 macOS DNS 設定
scutil --dns | grep "nameserver\[0\]"
```

## 預期結果

成功後應該看到：
- ✅ Port forward 進程在運行（2 個 socat 進程）
- ✅ 53 端口被 socat 占用（不是 mDNSResponder）
- ✅ `dig app.example.com` 返回 IP 地址（例如：172.20.0.10）
- ✅ macOS DNS 設定為 127.0.0.1

## 注意事項

1. **mDNSResponder 會自動重啟**：macOS 系統可能會自動重新啟動 mDNSResponder，如果發現問題，請重新執行修復腳本。

2. **測試完成後恢復**：
   ```bash
   # 停止 port forward
   sudo ./scripts/setup-dns-forward.sh stop
   
   # 恢復 mDNSResponder
   sudo launchctl load -w /System/Library/LaunchDaemons/com.apple.mDNSResponder.plist
   ```

3. **DNS 設定恢復**：測試完成後，記得將 macOS DNS 設定恢復為自動或您常用的 DNS 服務器。

## 如果問題仍然存在

如果以上方法都無法解決，請檢查：

1. **Docker 容器狀態**：
   ```bash
   docker ps --filter "name=dns-secondary"
   docker logs dns-secondary | tail -20
   ```

2. **端口映射**：
   ```bash
   docker port dns-secondary
   ```

3. **防火牆設定**：
   ```bash
   /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
   ```

4. **網路連接**：
   ```bash
   # 測試從主機到容器的連接
   nc -zv 127.0.0.1 5300
   ```

