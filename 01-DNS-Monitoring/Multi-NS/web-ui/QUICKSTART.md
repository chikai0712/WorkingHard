# Web UI 快速启动指南

## 🚀 快速开始

### 1. 确保 BIND DNS 容器正在运行

```bash
cd /Users/ckchiu/Desktop/Project/Multi-NS
docker-compose ps
```

如果未运行，启动它：
```bash
./start.sh
```

### 2. 启动 Web UI

```bash
cd web-ui
npm start
```

### 3. 打开浏览器

访问: **http://localhost:3000**

## 📋 功能说明

### ✅ 添加 DNS Zone
- 输入域名（例如: `test.example.com`）
- 输入 IP 地址（例如: `192.0.2.100`）
- 点击"添加 Zone"
- 系统会自动创建 zone 文件并重启 BIND

### 🔍 测试 DNS 查询
- 在测试框中输入域名
- 点击"查询"按钮
- 查看查询结果

### 📊 查看日志
- 点击"刷新日志"查看最近的 DNS 查询记录

### 🗑️ 删除 Zone
- 在现有 Zones 列表中点击"删除"按钮

## ⚠️ 注意事项

- 确保端口 3000 未被占用
- 需要 `dig` 命令来测试 DNS（macOS/Linux 通常已安装）
- 添加/删除 zone 后会自动重启 BIND 容器（可能需要几秒钟）

