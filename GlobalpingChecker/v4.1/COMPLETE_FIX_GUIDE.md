# 完整修复指南

## 当前状态

✅ 数据库已重新初始化，包含 498 个域名
✅ 代码已改进，支持更好的错误处理
❌ 应用需要重启以加载新数据
❌ 节点池需要重新拉取

## 手动修复步骤

### 第一步：重启应用

1. 打开终端，进入项目目录：
```bash
cd /Users/ckchiu/Desktop/Project/GlobalpingChecker/v4.1
```

2. 杀死现有的应用进程：
```bash
# 查找进程
lsof -i :8766

# 杀死进程（替换 PID）
kill -9 <PID>
```

3. 重新启动应用：
```bash
# 方法1：使用启动脚本
bash start.sh

# 方法2：直接运行
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8766 --reload
```

### 第二步：验证应用状态

重启后，访问 http://127.0.0.1:8766 并检查：
- 待分類应该显示 **498 个**（而不是 5 个）

### 第三步：拉取节点清单

在新的终端窗口中运行：
```bash
cd /Users/ckchiu/Desktop/Project/GlobalpingChecker/v4.1
python3 refresh_nodes.py
```

这个脚本会：
1. 连接到 Globalping API
2. 拉取所有在线的 probe 节点
3. 验证节点的地理位置
4. 保存到数据库

### 第四步：触发检测

应用重启后，点击"立即檢測"按钮或运行：
```bash
curl -X POST http://127.0.0.1:8766/api/check/trigger
```

## 故障排除

### 问题1：应用重启后仍然只显示 5 个域名

**原因**：应用启动时的工作目录不正确

**解决方案**：
```bash
# 确保从正确的目录启动
cd /Users/ckchiu/Desktop/Project/GlobalpingChecker/v4.1
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8766
```

### 问题2：节点拉取失败（403 Forbidden）

**原因**：API token 无效或网络问题

**检查步骤**：
1. 验证 .env 文件中的 token：
```bash
grep GLOBALPING_TOKEN .env
```

2. 测试 API 连接：
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" https://api.globalping.io/v1/probes
```

3. 如果 token 无效，从 https://app.globalping.io 获取新的 token

### 问题3：检测仍然返回 API_ERROR

**原因**：可能是 API token 问题或网络连接问题

**检查步骤**：
1. 查看应用日志中的错误信息
2. 确保网络连接正常
3. 验证 API token 有效

## 文件说明

- `refresh_nodes.py` - 重新拉取节点清单的脚本
- `init_domains.py` - 初始化域名的脚本
- `FIX_REPORT.md` - 修复报告
- `data/globalping_results.db` - 新的数据库文件
- `data/globalping_results.db.backup` - 旧的数据库备份

## 预期结果

完成以上步骤后：

1. ✅ 应用显示 498 个待分類的域名
2. ✅ 节点池包含多个已验证的节点
3. ✅ 检测能正确调用 Globalping API
4. ✅ 即時結果面板显示"使用節點"和"異常原因"

## 如果问题仍未解决

请检查：
1. Python 版本是否为 3.9+
2. 所有依赖是否已安装
3. 网络连接是否正常
4. API token 是否有效
5. 数据库文件是否可读写
