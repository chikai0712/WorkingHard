# 🔧 Cursor 連線 AWS 完整解決方案

## 問題說明

Cursor IDE 會自動設置代理（`http://127.0.0.1:xxxxx`），導致 AWS CLI 無法連線到 AWS 服務。

## ✅ 解決方案（3 種方法）

---

### 方法 1：使用系統終端（最簡單，推薦）

**優點**：無需任何配置，100% 可用

**步驟**：

1. 開啟系統終端（Terminal.app）
   - 按 `Cmd + Space`
   - 輸入 "Terminal"
   - 按 Enter

2. 執行檢查
   ```bash
   cd ~/Desktop/Project/AWS-deploy
   ./check-status.sh
   ```

3. 或使用一鍵腳本（在 Cursor 中執行）
   ```bash
   cd ~/Desktop/Project/AWS-deploy
   ./open-terminal-check.sh
   ```

---

### 方法 2：安裝 boto3 並使用 Python 腳本

**優點**：可以在 Cursor 中直接使用

**步驟**：

1. 安裝 boto3
   ```bash
   pip3 install --user boto3
   ```

2. 執行檢查
   ```bash
   cd ~/Desktop/Project/AWS-deploy
   python3 check-aws-boto3.py
   ```

**如果安裝失敗**，使用系統 Python：
```bash
/usr/bin/python3 -m pip install --user boto3
```

---

### 方法 3：配置 AWS CLI 使用 NO_PROXY

**優點**：一次配置，永久有效

**步驟**：

1. 編輯 AWS 配置
   ```bash
   nano ~/.aws/config
   ```

2. 添加以下內容
   ```ini
   [default]
   region = ap-northeast-1
   output = json
   no_proxy = *
   ```

3. 測試（在新終端執行）
   ```bash
   aws sts get-caller-identity
   ```

---

## 📊 當前狀態檢查

### 快速檢查命令

```bash
# 方法 1：系統終端
cd ~/Desktop/Project/AWS-deploy && ./check-status.sh

# 方法 2：Python（需要 boto3）
cd ~/Desktop/Project/AWS-deploy && python3 check-aws-boto3.py

# 方法 3：一鍵開啟系統終端
cd ~/Desktop/Project/AWS-deploy && ./open-terminal-check.sh
```

### 檢查會顯示

- ✅ AWS 連線狀態
- 📦 所有 EC2 實例列表
- 🟢 運行中的服務
- 💰 成本估算
- 💡 快速操作建議

---

## 🚀 部署和管理

### 在系統終端執行（推薦）

```bash
# 1. 開啟系統終端
open -a Terminal

# 2. 進入目錄
cd ~/Desktop/Project/AWS-deploy

# 3. 執行管理界面
./aws-manager.sh
```

### 可用操作

- **部署服務**：選項 1-3
- **檢查狀態**：選項 4-7
- **更新服務**：選項 8-10
- **管理實例**：選項 11-13

---

## 🔍 故障排除

### 問題 1：AWS CLI 仍然無法連線

**解決**：
```bash
# 在新終端執行
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY
aws sts get-caller-identity
```

### 問題 2：boto3 安裝失敗

**解決**：
```bash
# 使用系統 Python
/usr/bin/python3 -m pip install --user boto3

# 或使用 Homebrew Python
brew install python3
pip3 install boto3
```

### 問題 3：SSH 連線失敗

**解決**：
```bash
# 檢查密鑰權限
ls -la ~/.ssh/*.pem

# 修正權限
chmod 400 ~/.ssh/*.pem

# 執行修復腳本
cd ~/Desktop/Project/AWS-deploy
./fix-ssh-connection.sh
```

---

## 📝 已創建的工具

### 檢查工具
- `check-status.sh` - 完整狀態檢查（系統終端）
- `check-aws-boto3.py` - Python 版本（需要 boto3）
- `check-cursor.sh` - Cursor 版本（實驗性）
- `open-terminal-check.sh` - 一鍵開啟系統終端

### 管理工具
- `aws-manager.sh` - 統一管理界面
- `deploy-globalping-checker.sh` - 部署 Globalping
- `update-globalping-code.sh` - 更新代碼
- `update-globalping-domains.sh` - 更新域名列表

### 修復工具
- `fix-cursor-aws.sh` - 修復 Cursor AWS 連線
- `fix-ssh-connection.sh` - 修復 SSH 連線
- `check-environment.sh` - 環境檢查

---

## 💡 最佳實踐

### 日常使用

1. **檢查狀態**：在系統終端執行 `./check-status.sh`
2. **部署更新**：在系統終端執行 `./aws-manager.sh`
3. **快速操作**：使用 `./open-terminal-check.sh` 一鍵開啟

### 開發調試

1. 在 Cursor 中編輯代碼
2. 在系統終端執行部署
3. 使用 SSH 連線到 EC2 測試

### 成本控制

1. 定期檢查運行中的實例
2. 不使用時停止實例
3. 使用 `./aws-manager.sh` 選項 13 查看成本

---

## 🎯 推薦工作流程

```bash
# 1. 在 Cursor 中編輯代碼
# （正常使用 Cursor IDE）

# 2. 檢查 AWS 狀態（一鍵開啟系統終端）
cd ~/Desktop/Project/AWS-deploy
./open-terminal-check.sh

# 3. 在開啟的系統終端中執行部署
./aws-manager.sh
# 選擇需要的操作

# 4. 完成後關閉系統終端
# 繼續在 Cursor 中開發
```

---

## 📞 需要幫助？

### 檢查清單

- [ ] 已在系統終端（非 Cursor）執行
- [ ] AWS 憑證已配置（`aws configure`）
- [ ] 代理已禁用（`env | grep -i proxy` 無輸出）
- [ ] SSH 密鑰權限正確（`ls -la ~/.ssh/*.pem` 顯示 400）

### 快速診斷

```bash
# 在系統終端執行
cd ~/Desktop/Project/AWS-deploy
./check-environment.sh
```

---

## 📚 相關文檔

- [AWS 部署總覽](README.md)
- [故障排除指南](TROUBLESHOOTING.md)
- [狀態檢查指南](CHECK_STATUS_GUIDE.md)

---

**最後更新**: 2026-03-07  
**重要提醒**: 所有 AWS 操作建議在系統終端執行，避免 Cursor 代理問題！
