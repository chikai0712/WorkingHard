# AWS EC2 連線指令

## 📋 連線信息
- **IP 地址**: 54.238.247.106
- **端口**: 22 (SSH)
- **用戶**: ec2-user 或 ubuntu（取決於 AMI）
- **應用端口**: 8000

## 🔑 連線方式

### 方式 1：使用 SSH 密鑰（推薦）

```bash
# 假設你的密鑰文件是 your-key.pem
ssh -i /path/to/your-key.pem ec2-user@54.238.247.106

# 或如果是 Ubuntu AMI
ssh -i /path/to/your-key.pem ubuntu@54.238.247.106
```

### 方式 2：如果密鑰在 ~/.ssh 目錄

```bash
# 首先設置密鑰權限
chmod 400 ~/.ssh/your-key.pem

# 然後連線
ssh -i ~/.ssh/your-key.pem ec2-user@54.238.247.106
```

---

## 🚀 連線後的常用命令

### 1. 檢查應用狀態

```bash
# 檢查進程
ps aux | grep uvicorn

# 檢查端口
sudo netstat -tlnp | grep 8000

# 查看應用日誌
sudo journalctl -u globalping -f

# 或直接查看應用輸出
tail -f /opt/GlobalpingChecker/v4.1/app.log
```

### 2. 檢查應用是否運行

```bash
curl http://localhost:8000/api/stats
```

### 3. 生成模擬數據

```bash
cd /opt/GlobalpingChecker/v4.1
source venv/bin/activate
python generate_mock_data.py
```

### 4. 查看數據庫

```bash
cd /opt/GlobalpingChecker/v4.1
sqlite3 data/globalping_results.db

# 在 sqlite3 提示符中
SELECT COUNT(*) FROM domains;
SELECT COUNT(*) FROM test_batches;
SELECT COUNT(*) FROM domain_results;
.quit
```

### 5. 重啟應用

```bash
# 如果使用 systemd
sudo systemctl restart globalping

# 或查看狀態
sudo systemctl status globalping

# 查看日誌
sudo journalctl -u globalping -n 50
```

### 6. 查看應用配置

```bash
cat /opt/GlobalpingChecker/v4.1/.env
```

### 7. 檢查 Globalping API 連接

```bash
cd /opt/GlobalpingChecker/v4.1
source venv/bin/activate
python test_api_correct.py
```

---

## 📊 訪問監控頁面

### 本地訪問（在 AWS 實例上）
```bash
curl http://localhost:8000
```

### 遠程訪問（從你的電腦）
```
http://54.238.247.106:8000
```

---

## 🔧 故障排除

### 如果無法連線

```bash
# 檢查安全組規則
# 確保 22 端口（SSH）已開放

# 檢查密鑰文件權限
ls -la ~/.ssh/your-key.pem
# 應該顯示 -rw------- (400)

# 如果權限不對，修復
chmod 400 ~/.ssh/your-key.pem
```

### 如果應用無法訪問

```bash
# 檢查安全組規則
# 確保 8000 端口已開放

# 檢查應用是否運行
sudo systemctl status globalping

# 查看應用日誌
sudo journalctl -u globalping -f

# 檢查端口監聽
sudo netstat -tlnp | grep 8000
```

### 如果 API 無法連接

```bash
# 檢查網絡連接
ping api.globalping.io

# 測試 API
curl -X GET https://api.globalping.io/v1/limits \
  -H "Authorization: Bearer uh5vlg4ttg3v5gwby5zgtqrciimahql5"
```

---

## 💡 快速操作流程

```bash
# 1. 連線到 AWS
ssh -i ~/.ssh/your-key.pem ec2-user@54.238.247.106

# 2. 進入應用目錄
cd /opt/GlobalpingChecker/v4.1

# 3. 激活虛擬環境
source venv/bin/activate

# 4. 生成模擬數據
python generate_mock_data.py

# 5. 檢查應用狀態
curl http://localhost:8000/api/stats

# 6. 查看應用日誌
sudo journalctl -u globalping -f
```

---

## 📝 需要的信息

請提供以下信息以完成連線：

1. **SSH 密鑰文件位置** - 你的 `.pem` 文件在哪裡？
2. **AMI 類型** - 是 Amazon Linux 2 還是 Ubuntu？
3. **應用部署路徑** - 應用是否在 `/opt/GlobalpingChecker/v4.1`？

---

**準備好了嗎？提供上述信息，我可以幫你完成連線和配置！**
