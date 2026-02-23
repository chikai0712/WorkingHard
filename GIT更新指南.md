# Git 更新指南

## 常規更新流程

### 1. 檢查狀態
```bash
cd /Users/ckchiu/Desktop/Project
git status
```

### 2. 添加所有更改
```bash
git add -A
```
或添加特定檔案：
```bash
git add 檔案名稱
```

### 3. 提交更改
```bash
git commit -m "更新說明"
```

### 4. 推送到遠端
```bash
git push
```

---

## 遇到權限問題時的解決方案

如果遇到 `Operation not permitted` 或 `Unable to create index.lock` 錯誤：

### 方法 1：修復 .git 目錄權限
```bash
cd /Users/ckchiu/Desktop/Project
sudo chmod -R u+w .git
```

### 方法 2：移除 macOS 保護屬性
```bash
# 移除整個專案的保護屬性
cd /Users/ckchiu/Desktop
sudo xattr -d com.apple.provenance Project
sudo xattr -d com.apple.macl Project

# 移除 .git 目錄的保護屬性
cd /Users/ckchiu/Desktop/Project
sudo xattr -cr .git
```

### 方法 3：完整修復流程
```bash
cd /Users/ckchiu/Desktop/Project
sudo xattr -cr .git
sudo chmod -R u+w .git
git add -A
git commit -m "更新內容"
git push
```

---

## 快速更新腳本

創建一個快速更新腳本 `quick-git-update.sh`：

```bash
#!/bin/bash
cd /Users/ckchiu/Desktop/Project

# 檢查是否有權限問題
if ! git add -A 2>/dev/null; then
    echo "⚠️  偵測到權限問題，正在修復..."
    sudo chmod -R u+w .git
    git add -A
fi

# 提交
echo "📝 請輸入提交訊息："
read commit_message
git commit -m "$commit_message"

# 推送
echo "🚀 正在推送到遠端..."
git push

echo "✅ 更新完成！"
```

使用方式：
```bash
chmod +x quick-git-update.sh
./quick-git-update.sh
```

---

## 常用 Git 指令

### 查看提交歷史
```bash
git log --oneline -10
```

### 查看遠端倉庫
```bash
git remote -v
```

### 拉取最新更改
```bash
git pull
```

### 切換分支
```bash
git checkout 分支名稱
```

### 查看當前分支
```bash
git branch
```

### 創建新分支
```bash
git checkout -b 新分支名稱
```

---

## 注意事項

1. **權限問題**：如果專案是從雲端硬碟或外部硬碟複製來的，可能會有 macOS 保護屬性，需要先移除
2. **終端權限**：確保終端應用程式在「系統設定 > 隱私權與安全性 > 完整磁碟取用權限」中已啟用
3. **定期提交**：建議經常提交更改，避免一次提交太多檔案
4. **提交訊息**：使用清楚的提交訊息，方便日後查找

---

## 遠端倉庫資訊

- **倉庫 URL**: https://github.com/chikai0712/Unition.git
- **當前分支**: 2026-01-24-m8qd
- **主分支**: main

---

## 緊急情況處理

### 如果推送失敗
```bash
# 先拉取遠端更改
git pull --rebase

# 再推送
git push
```

### 如果需要放棄本地更改
```bash
# 放棄所有未提交的更改（危險！）
git reset --hard HEAD

# 放棄特定檔案的更改
git checkout -- 檔案名稱
```

### 如果需要撤銷最後一次提交
```bash
# 保留更改，只撤銷提交
git reset --soft HEAD~1

# 完全撤銷提交和更改（危險！）
git reset --hard HEAD~1
```

