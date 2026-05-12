# DNS 檢查工具 API 文檔

## 📋 概述

DNS 檢查工具提供命令行接口和 Python API，用於檢查域名解析結果是否在允許的白名單範圍內。

## 🔧 命令行接口

### 基本語法

```bash
dns_checker.py -R <domain> -S <nameserver> [OPTIONS]
```

### 參數說明

#### 必需參數

- `-R, --record`: 要檢查的域名（例如：example.com）
- `-S, --nameserver`: DNS 伺服器 IP 地址（例如：8.8.8.8）

#### 可選參數

- `-W, --whitelist`: 白名單文件名（相對於默認路徑 `/opt/dnsapi/`）
- `--whitelist-path`: 白名單文件完整路徑（覆蓋 `-W` 選項）
- `--whitelist-dir`: 白名單文件目錄（默認：`/opt/dnsapi/`）
- `-t, --timeout`: DNS 查詢超時時間（秒，默認：5）
- `-v, --verbose`: 詳細輸出（DEBUG 級別日誌）

### 使用範例

```bash
# 基本使用
python src/dns_checker_v2.py -R example.com -S 8.8.8.8

# 指定白名單文件
python src/dns_checker_v2.py -R example.com -S 8.8.8.8 -W custom_whitelist.txt

# 使用完整路徑
python src/dns_checker_v2.py -R example.com -S 8.8.8.8 \
    --whitelist-path /path/to/whitelist.txt

# 設置超時時間
python src/dns_checker_v2.py -R example.com -S 8.8.8.8 -t 10

# 詳細輸出
python src/dns_checker_v2.py -R example.com -S 8.8.8.8 -v
```

## 🐍 Python API

### DNSChecker 類

#### 初始化

```python
from dns_checker_v2 import DNSChecker

checker = DNSChecker(nameserver='8.8.8.8', timeout=5)
```

**參數**：
- `nameserver` (str): DNS 伺服器 IP 地址
- `timeout` (int): 查詢超時時間（秒，默認：5）

#### 方法

##### `check_domain(record, whitelist)`

檢查域名解析結果是否在白名單中。

**參數**：
- `record` (str): 要檢查的域名
- `whitelist` (List[str]): IP 白名單列表（CIDR 格式）

**返回**：
- `tuple`: (status, message, exit_code)
  - `status` (str): 'OK', 'CRITICAL', 'UNKNOWN'
  - `message` (str): 狀態消息
  - `exit_code` (int): 退出碼（0=OK, 2=CRITICAL, 3=UNKNOWN）

**範例**：
```python
whitelist = ['192.168.1.0/24', '10.0.0.0/8']
status, message, exit_code = checker.check_domain('example.com', whitelist)
print(f"Status: {status}, Exit Code: {exit_code}")
```

##### `is_ip_in_whitelist(ip, whitelist)`

檢查 IP 是否在白名單中。

**參數**：
- `ip` (str): IP 地址
- `whitelist` (List[str]): IP 白名單列表

**返回**：
- `bool`: True 如果 IP 在白名單中，False 否則

**範例**：
```python
whitelist = ['192.168.1.0/24']
result = checker.is_ip_in_whitelist('192.168.1.100', whitelist)
print(result)  # True
```

### 工具函數

#### `load_whitelist(whitelist_path)`

載入白名單文件。

**參數**：
- `whitelist_path` (str): 白名單文件路徑

**返回**：
- `List[str]`: 白名單列表

**異常**：
- `FileNotFoundError`: 文件不存在

**範例**：
```python
from dns_checker_v2 import load_whitelist

whitelist = load_whitelist('/opt/dnsapi/whitelist.txt')
```

#### `validate_nameserver(nameserver)`

驗證 nameserver IP 地址格式。

**參數**：
- `nameserver` (str): DNS 伺服器 IP 地址

**返回**：
- `bool`: True 如果格式正確，False 否則

**範例**：
```python
from dns_checker_v2 import validate_nameserver

if validate_nameserver('8.8.8.8'):
    print("有效的 IP 地址")
```

## 📊 退出碼

| 退出碼 | 狀態 | 說明 |
|--------|------|------|
| 0 | OK | 所有 IP 都在白名單中 |
| 2 | CRITICAL | 有 IP 不在白名單中 |
| 3 | UNKNOWN | 發生錯誤（DNS 錯誤、文件不存在等） |

## 📝 白名單格式

白名單文件支援以下格式：

```
# 這是註釋，會被忽略
192.168.1.0/24
10.0.0.0/8

# 空行也會被忽略
172.16.0.0/12

# 單個 IP（使用 /32）
8.8.8.8/32
```

**規則**：
- 每行一個 IP 地址或 CIDR 網絡範圍
- 以 `#` 開頭的行為註釋，會被忽略
- 空行會被忽略
- 支援 IPv4 和 IPv6（如果 Python 版本支援）

## 🔍 使用場景

### 1. Nagios/Icinga 監控

```bash
# 在 Nagios 配置中使用
command[check_dns]=/usr/local/bin/dns_checker.py -R $ARG1$ -S $ARG2$ -W $ARG3$
```

### 2. Cron 定時檢查

```bash
# 每 5 分鐘檢查一次
*/5 * * * * /usr/local/bin/dns_checker.py -R example.com -S 8.8.8.8
```

### 3. Python 腳本整合

```python
from dns_checker_v2 import DNSChecker, load_whitelist

checker = DNSChecker('8.8.8.8')
whitelist = load_whitelist('/opt/dnsapi/whitelist.txt')

status, message, exit_code = checker.check_domain('example.com', whitelist)
if exit_code != 0:
    send_alert(message)
```

---

**最後更新**：2025-01-XX

