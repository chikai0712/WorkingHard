# 修复检测失败问题 - 操作指南

## 问题诊断

你遇到的"全部检测失败，异常区 498"问题是由以下原因造成的：

1. **数据库损坏/锁定** - 之前的数据库文件已损坏，导致所有检测返回 API_ERROR
2. **域名加载问题** - 应用启动时只加载了 5 个测试域名，而不是完整的 498 个

## 已完成的修复

✅ 删除了损坏的数据库
✅ 创建了新的数据库并加载了 498 个域名
✅ 改进了错误处理代码，确保异常原因能正确显示
✅ 改进了即時結果面板，现在显示"使用節點"和"異常原因"两列

## 需要手动执行的步骤

### 1. 重启应用

在终端中执行：

```bash
cd /Users/ckchiu/Desktop/Project/GlobalpingChecker/v4.1

# 如果应用在运行，先杀死它
pkill -f "uvicorn app.main"

# 重新启动应用
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8766 --reload
```

或者使用启动脚本：

```bash
bash start.sh
```

### 2. 验证应用状态

重启后，访问 http://127.0.0.1:8766 并检查：

- 正常區应该显示 0 个
- 異常區应该显示 0 个  
- 待分類应该显示 498 个

### 3. 触发检测

点击"立即檢測"按钮或通过 API 触发：

```bash
curl -X POST http://127.0.0.1:8766/api/check/trigger
```

## 预期结果

重启后，应用应该：

1. 从数据库加载所有 498 个域名
2. 正确显示待分類的 498 个域名
3. 检测时正确调用 Globalping API
4. 在即時結果面板中显示"使用節點"和"異常原因"

## 如果问题仍然存在

如果重启后仍然只显示 5 个域名，可能是工作目录问题。请确保：

1. 应用从正确的目录启动（/Users/ckchiu/Desktop/Project/GlobalpingChecker/v4.1）
2. domains.txt 文件存在且包含 498 个域名
3. 数据库文件位置正确（data/globalping_results.db）

## 代码修改总结

### checker.py
- 改进了节点池查询的错误处理
- 添加了 `error_analysis` 字段到检测结果
- 改进了即時進度状态的数据结构

### dashboard.html
- 改进了即時結果面板的布局，现在显示两行
- 第一行：状态 + 域名
- 第二行：TOP排名 + ISP名称 + 异常原因

### main.py
- 添加了 `/api/domains/reload` 端点用于重新加载域名

## 数据库恢复

旧的数据库已备份到：
- data/globalping_results.db.backup
- data/globalping_results.db.reset_backup

新的数据库已创建并包含所有 498 个域名。
