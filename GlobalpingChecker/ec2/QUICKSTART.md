# EC2 快速部署指南

## 🎯 5 分鐘部署到 EC2

### 步驟 1: 創建 SSH Key (如果還沒有)

```bash
aws ec2 create-key-pair \
  --key-name globalping-checker \
  --query 'KeyMaterial' \
  --output text > globalping-checker.pem

chmod 400 globalping-checker.pem
```

### 步驟 2: 執行部署

```bash
cd ~/Desktop/Project/GlobalpingChecker/ec2
chmod +x deploy-ec2.sh
./deploy-ec2.sh
```

### 步驟 3: 連線到 EC2

```bash
# 使用生成的快速連線腳本
./connect.sh
```

### 步驟 4: 上傳項目文件

```bash
# 在本地執行
scp -i globalping-checker.pem -r ~/Desktop/Project/GlobalpingChecker ec2-user@YOUR_IP:~/
```

### 步驟 5: 執行安裝

```bash
# 在 EC2 上執行
cd ~/GlobalpingChecker/ec2
./setup.sh
```

### 步驟 6: 配置並測試

```bash
# 編輯配置
sudo nano /opt/globalping-checker/config.env

# 上傳域名
sudo nano /opt/globalping-checker/domains.txt

# 執行測試
/opt/globalping-checker/run_check.sh
```

## 🎉 完成！

系統已安裝完成，會按照 cron 排程自動執行。

## 📊 查看結果

```bash
# 查看日誌
tail -f /var/log/globalping-checker/check_*.log

# 查看 globalping 輸出
tail -f ~/globalping_*.log
```

## 🔧 常用命令

```bash
# 手動執行
/opt/globalping-checker/run_check.sh

# 查看定時任務
crontab -l

# 編輯配置
sudo nano /opt/globalping-checker/config.env

# 更新域名列表
sudo nano /opt/globalping-checker/domains.txt
```

## 💰 成本

- **免費方案**: $0/月 (前 12 個月)
- **之後**: ~$9.59/月 (t3.micro 24/7 運行)

## 📚 詳細文檔

查看 [README.md](README.md) 了解完整配置和進階功能。

---

**需要幫助？** 查看 README.md 或檢查日誌文件。
