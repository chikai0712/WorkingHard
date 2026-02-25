# AWS 部署檔案整理說明

## 📁 需要整理的檔案

以下 3 個檔案是 AWS 部署相關的腳本：

1. `check-game-status.sh` - 查看 EC2 實例狀態
2. `update-pokemon-game.sh` - 更新遊戲到 EC2
3. `deploy-pokemon-game.sh` - 完整部署新實例

## 🔧 手動整理步驟

由於系統權限限制，請手動執行以下步驟：

### 方法 1: 使用 Finder（推薦）

1. 打開 Finder，前往 `/Users/ckchiu/Desktop/Project`
2. 創建新資料夾，命名為 `AWS-deploy`
3. 將以下 3 個檔案拖入 `AWS-deploy` 資料夾：
   - check-game-status.sh
   - update-pokemon-game.sh
   - deploy-pokemon-game.sh

### 方法 2: 使用終端機

在終端機中執行：

```bash
cd ~/Desktop/Project
mkdir AWS-deploy
mv check-game-status.sh AWS-deploy/
mv update-pokemon-game.sh AWS-deploy/
mv deploy-pokemon-game.sh AWS-deploy/
```

## 📝 整理後的使用方式

整理完成後，使用以下命令執行腳本：

```bash
# 查看實例狀態
bash AWS-deploy/check-game-status.sh

# 更新遊戲內容
bash AWS-deploy/update-pokemon-game.sh

# 部署新實例
bash AWS-deploy/deploy-pokemon-game.sh
```

## ✅ 完成確認

整理完成後，你的專案結構應該是：

```
Project/
├── AWS-deploy/
│   ├── check-game-status.sh
│   ├── update-pokemon-game.sh
│   └── deploy-pokemon-game.sh
├── Ollie/
│   └── pokemon_game.html
└── (其他專案資料夾)
```

