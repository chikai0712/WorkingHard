# API Token 问题诊断

## 问题

节点拉取失败，API 返回 **403 Forbidden**

## 原因

当前的 Globalping API token 无效或已过期：
- Token: `uh5vlg4ttg3v5gwby5zgtqrciimahql5`
- 状态: ❌ 无效

## 解决方案

### 步骤 1：获取新的 API Token

1. 访问 https://app.globalping.io
2. 登录你的账户（如果没有账户，先注册）
3. 进入 API 设置或 Token 管理页面
4. 生成新的 API token
5. 复制新的 token

### 步骤 2：更新 .env 文件

编辑 `/Users/ckchiu/Desktop/Project/GlobalpingChecker/v4.1/.env` 文件：

```bash
# 找到这一行
GLOBALPING_TOKEN=uh5vlg4ttg3v5gwby5zgtqrciimahql5

# 替换为新的 token
GLOBALPING_TOKEN=YOUR_NEW_TOKEN_HERE
```

### 步骤 3：重启应用

```bash
cd /Users/ckchiu/Desktop/Project/GlobalpingChecker/v4.1

# 杀死现有进程
pkill -f "uvicorn app.main"

# 重新启动
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8766 --reload
```

### 步骤 4：重新拉取节点

```bash
/Users/ckchiu/Desktop/Project/GlobalpingChecker/v4.1/venv/bin/python3 refresh_nodes.py
```

## 验证 Token

如果你想验证新 token 是否有效，可以运行：

```bash
/Users/ckchiu/Desktop/Project/GlobalpingChecker/v4.1/venv/bin/python3 test_api_direct.py
```

如果看到 `✅ 成功获取 X 个 probe`，说明 token 有效。

## 常见问题

### Q: 我没有 Globalping 账户怎么办？

A: 访问 https://globalping.io 注册免费账户

### Q: Token 在哪里生成？

A: 通常在账户设置 → API Keys 或 Tokens 部分

### Q: Token 有有效期吗？

A: 取决于 Globalping 的政策，某些 token 可能会过期

### Q: 如何知道 token 是否有效？

A: 运行 `test_api_direct.py` 脚本进行测试

## 下一步

获取新 token 后：

1. ✅ 更新 .env 文件
2. ✅ 重启应用
3. ✅ 运行 `refresh_nodes.py` 拉取节点
4. ✅ 点击"立即檢測"开始检测

## 文件位置

- `.env` 文件: `/Users/ckchiu/Desktop/Project/GlobalpingChecker/v4.1/.env`
- 测试脚本: `/Users/ckchiu/Desktop/Project/GlobalpingChecker/v4.1/test_api_direct.py`
- 节点拉取脚本: `/Users/ckchiu/Desktop/Project/GlobalpingChecker/v4.1/refresh_nodes.py`
