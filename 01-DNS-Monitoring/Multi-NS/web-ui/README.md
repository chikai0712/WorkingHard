# BIND DNS Web 管理界面

简单的 Web 界面用于管理和测试 BIND DNS 服务器。

## 功能

- ✅ 查看现有 DNS zones
- ✅ 添加新的 DNS zone
- ✅ 删除 DNS zone
- ✅ 测试 DNS 查询
- ✅ 查看 DNS 查询日志
- ✅ 查看容器状态

## 安装和启动

### 1. 安装依赖

```bash
cd web-ui
npm install
```

### 2. 启动服务

```bash
npm start
```

服务将在 http://localhost:3000 运行

## 使用说明

1. **添加 Zone**: 输入域名和 IP 地址，点击"添加 Zone"
2. **测试查询**: 在测试框中输入域名，点击"查询"按钮
3. **查看日志**: 点击"刷新日志"查看最近的 DNS 查询记录
4. **删除 Zone**: 在现有 Zones 列表中点击"删除"按钮

## 注意事项

- 确保 BIND DNS 容器正在运行
- 添加或删除 zone 后会自动重启 BIND 容器
- 需要 `dig` 命令来测试 DNS 查询（macOS/Linux 通常已安装）

