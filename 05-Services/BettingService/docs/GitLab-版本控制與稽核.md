# GitLab 版本控制與稽核策略

## 📋 概述

本文件定義了注單服務系統在 GitLab 中的版本控制策略、代碼審查流程、稽核機制與權限管理規範。

## 🌿 Git 分支策略

### 分支模型：Git Flow

```
main (生產環境)
  │
  ├── release/v1.0.0 (發布分支)
  │     │
  │     └── hotfix/v1.0.1 (緊急修復)
  │
  └── develop (開發環境)
        │
        ├── feature/user-story-123 (功能分支)
        ├── feature/user-story-124
        └── bugfix/issue-456 (修復分支)
```

### 分支說明

#### 1. **main** (主分支)
- **用途**：生產環境代碼，永遠保持可部署狀態
- **保護規則**：
  - 禁止直接 Push
  - 必須通過 Merge Request
  - 至少 2 個審查者批准
  - 必須通過所有 CI/CD Pipeline
  - 禁止 Force Push
- **命名規範**：使用語義化版本號（Semantic Versioning）
  - 格式：`v1.0.0`, `v1.1.0`, `v2.0.0`
  - 標籤：每次發布必須打 Tag

#### 2. **develop** (開發分支)
- **用途**：開發環境代碼，功能整合分支
- **保護規則**：
  - 禁止直接 Push（Maintainer 除外）
  - 必須通過 Merge Request
  - 至少 1 個審查者批准
  - 必須通過 CI/CD Pipeline
- **合併來源**：feature/*, bugfix/*

#### 3. **feature/** (功能分支)
- **用途**：新功能開發
- **命名規範**：`feature/user-story-123`, `feature/add-order-validation`
- **生命週期**：
  - 從 `develop` 創建
  - 開發完成後合併回 `develop`
  - 合併後刪除分支
- **要求**：
  - 必須通過代碼審查
  - 必須通過單元測試
  - 必須更新文檔

#### 4. **bugfix/** (修復分支)
- **用途**：修復 Bug
- **命名規範**：`bugfix/issue-456`, `bugfix/fix-redis-connection`
- **生命週期**：
  - 從 `develop` 或 `main` 創建（視 Bug 嚴重程度）
  - 修復完成後合併回對應分支
  - 合併後刪除分支

#### 5. **release/** (發布分支)
- **用途**：準備發布新版本
- **命名規範**：`release/v1.0.0`
- **生命週期**：
  - 從 `develop` 創建
  - 僅進行 Bug 修復和文檔更新
  - 測試通過後合併到 `main` 和 `develop`
  - 在 `main` 上打 Tag

#### 6. **hotfix/** (緊急修復分支)
- **用途**：生產環境緊急修復
- **命名規範**：`hotfix/v1.0.1`
- **生命週期**：
  - 從 `main` 創建
  - 修復完成後合併到 `main` 和 `develop`
  - 在 `main` 上打 Tag

## 🔍 代碼審查流程

### Merge Request (MR) 流程

```
1. 開發者創建 MR
   ↓
2. 自動觸發 CI/CD Pipeline
   ↓
3. 代碼審查（至少 2 人，main 分支）
   ↓
4. 審查通過 → 合併
   ↓
5. 自動部署到對應環境
```

### MR 模板

```markdown
## 📝 變更說明

### 變更類型
- [ ] 新功能 (Feature)
- [ ] Bug 修復 (Bugfix)
- [ ] 文檔更新 (Documentation)
- [ ] 性能優化 (Performance)
- [ ] 重構 (Refactoring)
- [ ] 其他 (Other)

### 變更描述
<!-- 簡要說明本次變更的內容和目的 -->

### 相關 Issue
<!-- 關聯的 Issue 編號，格式：Closes #123 -->

### 測試說明
- [ ] 已添加單元測試
- [ ] 已添加整合測試
- [ ] 已進行手動測試
- [ ] 測試覆蓋率 ≥ 80%

### 檢查清單
- [ ] 代碼符合編碼規範
- [ ] 已更新相關文檔
- [ ] 已更新 CHANGELOG.md
- [ ] 無編譯錯誤和警告
- [ ] 已通過所有 CI/CD 檢查
- [ ] 已進行代碼自審

### 影響範圍
<!-- 說明本次變更可能影響的範圍 -->

### 截圖/演示
<!-- 如有 UI 變更，請附上截圖或演示連結 -->
```

### 代碼審查檢查清單

#### 功能檢查
- [ ] 功能實現符合需求
- [ ] 邊界條件處理正確
- [ ] 錯誤處理完善
- [ ] 日誌記錄適當

#### 代碼質量
- [ ] 代碼可讀性良好
- [ ] 命名規範統一
- [ ] 無重複代碼
- [ ] 函數長度適中（< 50 行）
- [ ] 複雜度適中（Cyclomatic Complexity < 10）

#### 安全性
- [ ] 無 SQL 注入風險
- [ ] 無 XSS 風險
- [ ] 敏感信息已加密
- [ ] 輸入驗證完善
- [ ] 權限檢查正確

#### 性能
- [ ] 無性能瓶頸
- [ ] 數據庫查詢優化
- [ ] 緩存使用合理
- [ ] 無內存洩漏

#### 測試
- [ ] 單元測試覆蓋率 ≥ 80%
- [ ] 整合測試完整
- [ ] 測試用例有意義

## 📊 稽核機制

### 1. 代碼變更稽核

#### GitLab Audit Events

GitLab 自動記錄以下事件：
- 代碼 Push
- Merge Request 創建/合併
- 分支創建/刪除
- Tag 創建
- 保護分支變更
- 權限變更

#### 自定義稽核日誌

```yaml
# .gitlab-ci.yml 中的稽核記錄
audit:
  stage: audit
  script:
    - |
      echo "稽核記錄:"
      echo "  - 提交者: $GITLAB_USER_NAME"
      echo "  - 提交時間: $(date)"
      echo "  - 分支: $CI_COMMIT_REF_NAME"
      echo "  - Commit: $CI_COMMIT_SHA"
      echo "  - 變更文件數: $(git diff --name-only $CI_COMMIT_BEFORE_SHA $CI_COMMIT_SHA | wc -l)"
    - |
      # 記錄到稽核系統
      curl -X POST https://audit-system.example.com/api/events \
        -H "Content-Type: application/json" \
        -d "{
          \"event_type\": \"code_change\",
          \"user\": \"$GITLAB_USER_NAME\",
          \"timestamp\": \"$(date -Iseconds)\",
          \"branch\": \"$CI_COMMIT_REF_NAME\",
          \"commit\": \"$CI_COMMIT_SHA\",
          \"files_changed\": $(git diff --name-only $CI_COMMIT_BEFORE_SHA $CI_COMMIT_SHA | wc -l)
        }"
  only:
    - main
    - develop
```

### 2. 合規性檢查

#### 代碼掃描

```yaml
# .gitlab-ci.yml
code_scan:
  stage: test
  image: golangci/golangci-lint:latest
  script:
    - golangci-lint run ./...
    - |
      # 檢查敏感信息
      if grep -r "password\|secret\|api_key" --include="*.go" .; then
        echo "❌ 發現可能的敏感信息"
        exit 1
      fi
  artifacts:
    reports:
      codequality: gl-codequality.json
```

#### 依賴掃描

```yaml
dependency_scan:
  stage: test
  image: aquasec/trivy:latest
  script:
    - trivy fs --severity HIGH,CRITICAL .
    - trivy image --severity HIGH,CRITICAL $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  allow_failure: true
```

#### 安全掃描

```yaml
security_scan:
  stage: test
  image: securego/gosec:latest
  script:
    - gosec -fmt json -out gosec-report.json ./...
  artifacts:
    reports:
      sast: gosec-report.json
```

### 3. 稽核日誌查詢

#### GitLab API 查詢

```bash
# 查詢特定用戶的操作記錄
curl --header "PRIVATE-TOKEN: <your-token>" \
  "https://gitlab.example.com/api/v4/audit_events?entity_type=User&entity_id=123"

# 查詢項目的變更記錄
curl --header "PRIVATE-TOKEN: <your-token>" \
  "https://gitlab.example.com/api/v4/projects/123/audit_events"
```

#### 自定義稽核查詢腳本

```bash
#!/bin/bash
# scripts/audit_query.sh

PROJECT_ID=$1
START_DATE=$2
END_DATE=$3

curl --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://gitlab.example.com/api/v4/projects/$PROJECT_ID/audit_events?created_after=$START_DATE&created_before=$END_DATE" \
  | jq '.[] | {user: .user.name, action: .details.action, timestamp: .created_at}'
```

## 🔐 權限管理

### 角色定義

#### 1. **Owner** (所有者)
- 所有權限
- 可刪除項目
- 可轉移項目

#### 2. **Maintainer** (維護者)
- 可合併到 main/develop
- 可管理分支保護規則
- 可管理 CI/CD 變量
- 可管理成員權限

#### 3. **Developer** (開發者)
- 可創建分支
- 可創建 Merge Request
- 可審查代碼
- 可推送到非保護分支

#### 4. **Reporter** (報告者)
- 可查看代碼
- 可查看 CI/CD 結果
- 可創建 Issue

#### 5. **Guest** (訪客)
- 僅可查看項目

### 分支保護規則

#### main 分支保護

```yaml
# 通過 GitLab API 設置
curl --request PUT \
  --header "PRIVATE-TOKEN: <token>" \
  --header "Content-Type: application/json" \
  --data '{
    "name": "main",
    "push_access_levels": [{"access_level": 0}],
    "merge_access_levels": [{"access_level": 40}],
    "allow_force_push": false,
    "code_owner_approval_required": true,
    "required_approvals": 2
  }' \
  "https://gitlab.example.com/api/v4/projects/123/protected_branches/main"
```

#### develop 分支保護

```yaml
{
  "name": "develop",
  "push_access_levels": [{"access_level": 40}],  # Maintainer only
  "merge_access_levels": [{"access_level": 30}],  # Developer
  "allow_force_push": false,
  "required_approvals": 1
}
```

### CODEOWNERS 文件

```bash
# .gitlab/CODEOWNERS

# 核心業務邏輯
/internal/order/          @team-lead @senior-dev
/internal/gateway/        @team-lead @senior-dev

# 基礎設施
/deploy/kubernetes/        @devops-lead @infra-team
/deploy/docker/            @devops-lead @infra-team

# 配置和文檔
/configs/                  @team-lead
/docs/                     @tech-writer @team-lead

# 所有 Go 文件
*.go                       @team-lead @senior-dev

# CI/CD 配置
.gitlab-ci.yml             @devops-lead @team-lead
```

## 📈 稽核報告

### 每日稽核報告

```bash
#!/bin/bash
# scripts/daily_audit_report.sh

PROJECT_ID=$1
DATE=$(date -d yesterday +%Y-%m-%d)

echo "=== 每日稽核報告 ===" > audit_report.txt
echo "日期: $DATE" >> audit_report.txt
echo "" >> audit_report.txt

# 代碼變更統計
echo "代碼變更統計:" >> audit_report.txt
git log --since="$DATE 00:00:00" --until="$DATE 23:59:59" --pretty=format:"%h - %an, %ar : %s" >> audit_report.txt

# Merge Request 統計
echo "" >> audit_report.txt
echo "Merge Request 統計:" >> audit_report.txt
curl --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://gitlab.example.com/api/v4/projects/$PROJECT_ID/merge_requests?created_after=$DATE" \
  | jq '.[] | {author: .author.name, title: .title, state: .state}' >> audit_report.txt

# 發送報告
mail -s "每日稽核報告 - $DATE" team@example.com < audit_report.txt
```

### 合規性報告

```yaml
# .gitlab-ci.yml
compliance_report:
  stage: deploy
  script:
    - |
      echo "=== 合規性報告 ===" > compliance_report.txt
      echo "日期: $(date)" >> compliance_report.txt
      echo "" >> compliance_report.txt
      echo "代碼掃描結果:" >> compliance_report.txt
      cat gl-codequality.json >> compliance_report.txt
      echo "" >> compliance_report.txt
      echo "安全掃描結果:" >> compliance_report.txt
      cat gosec-report.json >> compliance_report.txt
    - |
      # 上傳到合規系統
      curl -X POST https://compliance.example.com/api/reports \
        -H "Content-Type: application/json" \
        -d @compliance_report.txt
  only:
    - main
  when: always
```

## 🚨 違規處理

### 自動化違規檢測

```yaml
# .gitlab-ci.yml
violation_check:
  stage: test
  script:
    - |
      # 檢查是否直接推送到保護分支
      if [ "$CI_COMMIT_REF_NAME" = "main" ] && [ "$CI_COMMIT_BRANCH" != "" ]; then
        echo "❌ 禁止直接推送到 main 分支"
        exit 1
      fi
      
      # 檢查 Commit 信息格式
      if ! echo "$CI_COMMIT_MESSAGE" | grep -qE "^(feat|fix|docs|style|refactor|test|chore):"; then
        echo "❌ Commit 信息格式不正確，應使用: type: description"
        exit 1
      fi
      
      # 檢查是否包含敏感信息
      if git diff --cached | grep -iE "password|secret|api_key|token" | grep -vE "^\+\+\+|^---|^@@"; then
        echo "❌ 檢測到可能的敏感信息"
        exit 1
      fi
```

### 違規通知

```yaml
violation_notify:
  stage: deploy
  script:
    - |
      curl -X POST https://slack.example.com/api/webhook \
        -H "Content-Type: application/json" \
        -d "{
          \"text\": \"⚠️ 檢測到違規操作\",
          \"attachments\": [{
            \"color\": \"danger\",
            \"fields\": [{
              \"title\": \"用戶\",
              \"value\": \"$GITLAB_USER_NAME\",
              \"short\": true
            }, {
              \"title\": \"操作\",
              \"value\": \"$CI_COMMIT_MESSAGE\",
              \"short\": true
            }]
          }]
        }"
  when: on_failure
```

## 📝 最佳實踐

1. **Commit 規範**
   - 使用 Conventional Commits 格式
   - 格式：`type(scope): description`
   - 類型：feat, fix, docs, style, refactor, test, chore

2. **分支命名**
   - 功能分支：`feature/user-story-123`
   - 修復分支：`bugfix/issue-456`
   - 發布分支：`release/v1.0.0`

3. **代碼審查**
   - 至少 2 人審查（main 分支）
   - 審查時間不超過 24 小時
   - 使用 MR 模板確保完整性

4. **稽核日誌**
   - 所有操作自動記錄
   - 定期生成稽核報告
   - 保留至少 1 年

5. **權限管理**
   - 最小權限原則
   - 定期審查權限
   - 使用 CODEOWNERS 確保審查質量

---

**最後更新**：2025-01-XX

