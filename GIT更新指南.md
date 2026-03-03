# Git 更新指南

## ⭐ 重要提醒：先 Pull 再 Push！

**正確的工作流程：**
```bash
# 1. 開始工作前，先拉取遠端最新更改
git pull --rebase

# 2. 進行你的修改...

# 3. 提交更改
git add -A
git commit -m "更新說明"

# 4. 推送前再次確認（可選但推薦）
git pull --rebase

# 5. 推送
git push
```

**為什麼要先 pull？**
- ✅ 避免歷史分叉，不需要強制推送
- ✅ 及早在本地發現和解決衝突
- ✅ 確保在最新的程式碼基礎上工作
- ✅ 避免覆蓋別人的更改

---

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

## 推送被拒絕的處理方式

### 錯誤訊息
```
! [rejected]        2026-01-24-m8qd -> 2026-01-24-m8qd (non-fast-forward)
error: failed to push some refs to 'https://github.com/chikai0712/Unition.git'
hint: Updates were rejected because the tip of your current branch is behind
hint: its remote counterpart.
```

這表示遠端分支有新的提交，你需要先同步遠端更改。

### 解決方法 1：使用 Rebase（推薦）

Rebase 會讓提交歷史保持線性，更整潔。

```bash
cd /Users/ckchiu/Desktop/Project

# 拉取並 rebase
git pull --rebase

# 如果沒有衝突，直接推送
git push
```

**如果有衝突：**
```bash
# Git 會告訴你哪些檔案有衝突
# 1. 打開衝突檔案，尋找並解決衝突標記：
#    <<<<<<< HEAD
#    你的更改
#    =======
#    遠端的更改
#    >>>>>>> commit-hash

# 2. 解決衝突後，標記為已解決
git add 衝突檔案名稱

# 3. 繼續 rebase
git rebase --continue

# 4. 推送
git push
```

**如果想放棄 rebase：**
```bash
git rebase --abort
```

### 解決方法 2：使用 Merge（較簡單）

Merge 會創建一個合併提交，歷史會有分支。

```bash
cd /Users/ckchiu/Desktop/Project

# 拉取並合併
git pull

# 如果沒有衝突，直接推送
git push
```

**如果有衝突：**
```bash
# 1. 解決衝突檔案中的標記
# 2. 標記為已解決
git add 衝突檔案名稱

# 3. 完成合併
git commit

# 4. 推送
git push
```

### 解決方法 3：強制推送（需謹慎使用）

⚠️ **警告**：這會覆蓋遠端的更改，只在確定要丟棄遠端更改時使用！

```bash
# 推薦：更安全的強制推送（不會覆蓋別人的新提交）
git push --force-with-lease

# 不推薦：無條件強制推送（可能丟失別人的提交）
git push --force
```

---

## 為什麼需要強制推送？

### 常見原因

#### 1. 提交歷史被改寫
當你使用以下命令時，會改變提交的 hash 值：
- `git commit --amend`：修改最後一次提交
- `git rebase`：重新整理提交歷史
- `git reset`：重置提交

這會導致本地和遠端的歷史不一致，Git 無法自動合併。

**範例：**
```
遠端: A -> B -> C
本地: A -> B -> D

C 和 D 是不同的提交，歷史分叉了
```

#### 2. 在多個地方同時工作
- 在不同電腦上工作
- 有其他協作者推送了新提交
- 但你的本地歷史已經分叉

#### 3. 衝突的提交歷史
```
遠端: A -> B -> C (commit hash: b24c247)
本地: A -> B -> D (commit hash: 761482e)

Git 不知道該保留 C 還是 D
```

### `--force` vs `--force-with-lease` 的區別

| 命令 | 行為 | 安全性 | 使用場景 |
|------|------|--------|----------|
| `git push --force` | 無條件覆蓋遠端 | ⚠️ 危險 | 個人分支，確定沒有其他人的提交 |
| `git push --force-with-lease` | 只在遠端沒有新提交時覆蓋 | ✅ 較安全 | **推薦使用**，可防止意外覆蓋 |

**`--force-with-lease` 的保護機制：**
```bash
# 如果遠端有你不知道的新提交，會拒絕推送
git push --force-with-lease
# 輸出：! [rejected] ... (stale info)

# 這時你可以先拉取查看
git fetch
git log origin/分支名稱
```

### 如何避免需要強制推送？

#### 1. 開始工作前先同步
```bash
# 每次開始工作前
git pull --rebase
```

#### 2. 不要改寫已推送的歷史
```bash
# ❌ 避免對已推送的提交使用：
git commit --amend
git rebase -i
git reset --hard

# ✅ 如果需要修改，使用新的提交
git commit -m "修正之前的錯誤"
```

#### 3. 使用功能分支
```bash
# 在新分支上實驗性工作
git checkout -b feature-branch

# 完成後合併到主分支
git checkout main
git merge feature-branch
```

#### 4. 定期推送
```bash
# 經常推送，避免本地和遠端差距太大
git push
```

### 實際案例分析

**你的情況：**
```
+ b24c247...761482e 2026-01-24-m8qd -> 2026-01-24-m8qd (forced update)
```

**解讀：**
- 遠端原本的提交：`b24c247`
- 你的本地提交：`761482e`
- 使用 `--force-with-lease` 成功推送 ✅

**可能的原因：**
1. 你在另一台電腦或之前推送過 `b24c247`
2. 後來在本地做了修改，產生了新的提交 `761482e`
3. 兩個提交歷史不同，需要強制推送

### 團隊協作時的注意事項

#### 個人分支
```bash
# 在自己的分支上可以安全使用
git push --force-with-lease
```

#### 共享分支（如 main、develop）
```bash
# ❌ 不要在共享分支上強制推送！
# 會影響其他團隊成員

# ✅ 應該使用 pull request / merge request
git checkout -b fix-branch
git push origin fix-branch
# 然後在 GitHub 上創建 PR
```

### 強制推送後的恢復

如果不小心強制推送了錯誤的內容：

```bash
# 1. 查看 reflog 找到之前的提交
git reflog

# 2. 恢復到之前的狀態
git reset --hard HEAD@{n}  # n 是 reflog 中的編號

# 3. 再次強制推送正確的版本
git push --force-with-lease
```

---

## 衝突解決步驟詳解

### 1. 識別衝突檔案
```bash
git status
# 會顯示 "both modified" 的檔案
```

### 2. 打開衝突檔案
衝突標記看起來像這樣：
```
<<<<<<< HEAD
你的本地更改
=======
遠端的更改
>>>>>>> origin/2026-01-24-m8qd
```

### 3. 解決衝突
- 保留你的更改：刪除 `=======` 到 `>>>>>>>` 之間的內容
- 保留遠端更改：刪除 `<<<<<<<` 到 `=======` 之間的內容
- 保留兩者：手動整合兩邊的更改
- 刪除所有衝突標記（`<<<<<<<`, `=======`, `>>>>>>>`）

### 4. 標記為已解決
```bash
git add 已解決的檔案
```

### 5. 完成操作
```bash
# 如果是 rebase
git rebase --continue

# 如果是 merge
git commit
```

### 6. 推送
```bash
git push
```

---

## 緊急情況處理

### 如果推送失敗（已處理，見上方）
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

### 如果 rebase 過程中出錯
```bash
# 放棄 rebase，回到原始狀態
git rebase --abort

# 跳過當前衝突的提交（謹慎使用）
git rebase --skip
```

### 查看衝突狀態
```bash
# 查看哪些檔案有衝突
git status

# 查看衝突的詳細內容
git diff

# 查看遠端和本地的差異
git log --oneline --graph --all
```

