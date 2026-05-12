# BIND DNS 容器快速開始指南

## 🚀 一鍵啟動

### macOS/Linux
```bash
./start.sh
```

### Windows
```cmd
start.bat
```

### 使用 Makefile (推薦)
```bash
make start
```

---

## 🧪 測試 DNS

```bash
# 使用測試腳本
./test-dns.sh

# 或使用 Makefile
make test

# 或手動測試
dig @127.0.0.1 example.com
```

---

## 📝 添加新域名

```bash
# 使用輔助腳本
./add-zone.sh example.com 192.0.2.100

# 然後重啟容器
docker-compose restart bind9
```

---

## 📊 常用命令

```bash
# 查看狀態
make status
# 或
docker-compose ps

# 查看日誌
make logs
# 或
docker-compose logs -f bind9

# 停止服務
make stop
# 或
./stop.sh

# 重啟服務
make restart
```

---

## 🔍 檢查配置

```bash
# 檢查配置文件語法
make checkconf

# 檢查 Zone 文件
docker exec -it bind9-dns named-checkzone example.com /var/lib/bind/zones/db.example.com
```

---

## 📚 詳細文檔

- [完整使用指南](./BIND_DNS_使用指南.md)
- [快速參考](./README_BIND.md)

---

**提示**: 使用 `make help` 查看所有可用命令

