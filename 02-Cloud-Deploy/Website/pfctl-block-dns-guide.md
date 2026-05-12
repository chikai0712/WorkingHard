# macOS pfctl 封鎖 DNS 正確方法

## ❌ 問題分析

從你的輸出可以看到：
1. `pfctl -a custom -f -` 執行但沒有錯誤
2. `pfctl -sr | grep 205.251.197.44` 沒有找到規則
3. `dig @205.251.197.44` 仍然成功（表示沒有被封鎖）

**結論：封鎖規則沒有正確應用**

---

## ✅ 正確的封鎖方法

### 方法 1：使用 anchor（推薦）

```bash
# 1. 創建 anchor 規則文件
echo 'block drop out quick proto udp from any to 205.251.197.44 port 53' | \
    sudo pfctl -a custom -f -

# 2. 驗證規則
sudo pfctl -a custom -sr

# 3. 測試封鎖
dig @205.251.197.44 www.clouddeployment168.site +time=2
# 應該失敗或超時
```

### 方法 2：使用臨時規則文件

```bash
# 1. 創建規則文件
cat > /tmp/block_dns.conf << 'EOF'
block drop out quick proto udp from any to 205.251.197.44 port 53
EOF

# 2. 載入規則
sudo pfctl -a custom -f /tmp/block_dns.conf

# 3. 驗證
sudo pfctl -a custom -sr
```

### 方法 3：添加到現有規則（如果 pfctl 已啟用）

```bash
# 1. 查看現有規則
sudo pfctl -sr

# 2. 添加封鎖規則（保留現有規則）
(sudo pfctl -sr; echo 'block drop out quick proto udp from any to 205.251.197.44 port 53') | \
    sudo pfctl -f -

# 3. 驗證
sudo pfctl -sr | grep 205.251.197.44
```

---

## 🔧 完整測試流程

### 步驟 1：確保 pfctl 已啟用

```bash
# 檢查狀態
sudo pfctl -si | grep Status

# 如果未啟用，啟用它
sudo pfctl -e
```

### 步驟 2：封鎖 DNS

```bash
# 方法 A：使用 anchor（推薦）
echo 'block drop out quick proto udp from any to 205.251.197.44 port 53' | \
    sudo pfctl -a custom -f -

# 方法 B：如果方法 A 失敗，使用這個
sudo pfctl -a custom -f - << 'EOF'
block drop out quick proto udp from any to 205.251.197.44 port 53
EOF
```

### 步驟 3：驗證封鎖

```bash
# 檢查規則是否存在
sudo pfctl -a custom -sr
# 應該看到：block drop out quick proto udp from any to 205.251.197.44 port 53

# 如果看不到，檢查所有規則
sudo pfctl -sr | grep 205.251.197.44

# 測試封鎖
dig @205.251.197.44 www.clouddeployment168.site +time=2
# 應該失敗或超時
```

### 步驟 4：清除快取並測試

```bash
# 清除 DNS 快取
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder

# 開啟 Wireshark，過濾器：dns || icmp

# 執行查詢（不指定 DNS）
nslookup www.clouddeployment168.site
```

### 步驟 5：解除封鎖

```bash
# 清除 anchor 規則
sudo pfctl -a custom -F all

# 或重新載入原始配置
sudo pfctl -f /etc/pf.conf
```

---

## 🐛 故障排除

### 問題 1：規則沒有顯示

**可能原因：**
- anchor 名稱不對
- 規則語法錯誤
- pfctl 未啟用

**解決方法：**
```bash
# 檢查 pfctl 狀態
sudo pfctl -si

# 檢查所有 anchor
sudo pfctl -sA

# 檢查 anchor 中的規則
sudo pfctl -a custom -sr
```

### 問題 2：封鎖後仍然可以查詢

**可能原因：**
- 規則沒有正確應用
- DNS 快取
- 規則語法錯誤

**解決方法：**
```bash
# 1. 確認規則存在
sudo pfctl -a custom -sr

# 2. 清除快取
sudo dscacheutil -flushcache

# 3. 測試（應該失敗）
dig @205.251.197.44 www.clouddeployment168.site +time=2

# 4. 如果還是成功，檢查規則語法
# 正確語法：block drop out quick proto udp from any to 205.251.197.44 port 53
```

### 問題 3：pfctl 警告

**警告訊息：**
```
pfctl: Use of -f option, could result in flushing of rules
```

**說明：**
- 這是警告，不是錯誤
- 使用 `-a custom` 只影響 custom anchor，不會清除主規則集
- 可以安全忽略

---

## 📝 改進的封鎖腳本

創建一個更可靠的封鎖腳本：

```bash
#!/bin/bash

DNS_IP="205.251.197.44"
ANCHOR="custom"

echo "封鎖 DNS: $DNS_IP"

# 確保 pfctl 已啟用
if ! sudo pfctl -si 2>/dev/null | grep -q "Status: Enabled"; then
    echo "啟用 pfctl..."
    sudo pfctl -e
fi

# 封鎖 DNS
echo "block drop out quick proto udp from any to $DNS_IP port 53" | \
    sudo pfctl -a $ANCHOR -f -

# 驗證
if sudo pfctl -a $ANCHOR -sr 2>/dev/null | grep -q "$DNS_IP"; then
    echo "✅ 封鎖成功"
    sudo pfctl -a $ANCHOR -sr | grep "$DNS_IP"
else
    echo "❌ 封鎖失敗"
    echo "嘗試其他方法..."
    
    # 備用方法
    (sudo pfctl -sr 2>/dev/null; \
     echo "block drop out quick proto udp from any to $DNS_IP port 53") | \
        sudo pfctl -f -
    
    if sudo pfctl -sr 2>/dev/null | grep -q "$DNS_IP"; then
        echo "✅ 封鎖成功（使用備用方法）"
    else
        echo "❌ 封鎖失敗，請手動檢查"
    fi
fi
```

---

## 🎯 快速測試命令

```bash
# 1. 封鎖
echo 'block drop out quick proto udp from any to 205.251.197.44 port 53' | \
    sudo pfctl -a custom -f -

# 2. 驗證
sudo pfctl -a custom -sr

# 3. 測試（應該失敗）
dig @205.251.197.44 www.clouddeployment168.site +time=2

# 4. 解除
sudo pfctl -a custom -F all
```

---

## 💡 重要提示

1. **使用 anchor**：`-a custom` 避免影響主規則集
2. **驗證規則**：使用 `pfctl -a custom -sr` 檢查
3. **清除快取**：測試前清除 DNS 快取
4. **測試封鎖**：使用 `dig @IP` 直接測試被封鎖的 DNS

---

## ✅ 檢查清單

封鎖 DNS 前，確認：

- [ ] pfctl 已啟用：`sudo pfctl -si | grep Status`
- [ ] 規則已添加：`sudo pfctl -a custom -sr`
- [ ] 封鎖生效：`dig @IP` 失敗或超時
- [ ] DNS 快取已清除：`sudo dscacheutil -flushcache`
- [ ] Wireshark 已開啟：過濾器 `dns || icmp`

完成這些步驟後，應該可以在 Wireshark 中看到故障切換行為。
