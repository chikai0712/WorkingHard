# BIND DNS 容器快速指南

## 🚀 快速啟動

### macOS/Linux
```bash
chmod +x start.sh
./start.sh
```

### Windows
```cmd
start.bat
```

### 或使用 Docker Compose
```bash
docker-compose up -d
```

## 📝 基本使用

### 測試 DNS
```bash
# 查詢 A 記錄
dig @127.0.0.1 example.com

# 或使用 nslookup
nslookup example.com 127.0.0.1
```

### 查看日誌
```bash
docker-compose logs -f bind9
```

### 停止服務
```bash
docker-compose down
```

## 📁 配置文件位置

- **主配置**: `bind/config/named.conf`
- **Zone 配置**: `bind/config/named.conf.local`
- **Zone 文件**: `bind/zones/`
- **日誌**: `bind/logs/`

## 🔧 添加新 Zone

### 方法 1: 使用 Web 界面（推薦）python3 xe_scraper.py

1. 啟動 Web UI:
   ```bash
   cd web-ui
   npm install
   npm start
   ```
2. 打開瀏覽器訪問 http://localhost:3000
3. 在界面中添加域名和 IP 地址即可

### 方法 2: 手動添加

1. 在 `bind/zones/` 創建 Zone 文件
2. 在 `bind/config/named.conf.local` 添加 Zone 配置
3. 重啟容器: `docker-compose restart bind9`

詳細說明請參考 [BIND_DNS_使用指南.md](./BIND_DNS_使用指南.md)

