# CI/CD Practical Skeleton

此目錄提供可套用模板層級的 CI/CD 範例。

## Files
- `.env.example`: local skeleton configuration
- `pipeline.sh`: local helper / metadata viewer
- `github-actions-example.yml`: GitHub Actions pipeline template
- `gitlab-ci-example.yml`: GitLab CI pipeline template
- `Jenkinsfile.example`: Jenkins declarative pipeline template
- `jenkins-pipeline.example.yaml`: Jenkins pipeline parameter / credential example
- `notifications.example.yaml`: Slack / Jira notification example

## Included stages
- source gate
- security gate
- build
- artifact upload/package
- deploy gate
- post-deploy health gate

## Design Principles

### Build 與 Deploy Gate 分離
這裡把 `lint / test / build / artifact` 放在同一條驗證鏈，但把 deploy 保留成 gate。原因是建置成功不等於適合部署，正式環境通常還需要人工核准、change window、smoke test 或風險確認。

### Pipeline 是驗證層，不是業務邏輯層
CI/CD 應負責驗證與交付，不應在 workflow 內硬編太多業務判斷。這樣做可以降低 pipeline 與應用本身耦合，讓同一套模板可複用到不同專案。

### Artifact 優先
這個目錄假設「可重複部署的交付物」比「每次臨時重新建置」更重要。先產出 artifact，再交給 release/deploy 決策層，可以讓 rollback、追版本與稽核更簡單。

### Shared Gates 先於正式變更
CI 入口層現在先對齊 shared gate framework：
- source gate：lint / test / artifact metadata
- security gate：secret scanning / SAST / vulnerability scan
- post-deploy health gate：smoke test / health verification / rollback decision

這讓 Jenkins 與 GitHub workflow 都能使用同一套 `pass / hold / block / rollback / fallback` 治理語言。

## Typical Flow
1. Checkout 原始碼
2. 執行 source gate
3. 執行 security gate
4. 建立 artifact
5. 上傳 artifact 或 package metadata
6. 進入 deploy gate
7. deploy 後執行 post-deploy health gate

## Sequence Flow
1. 開發者提交變更
2. CI provider 啟動 pipeline
3. Pipeline 執行 source gate
4. Pipeline 執行 security gate
5. 產生 artifact 並保存 metadata
6. 若條件符合，進入 deploy gate
7. deploy 後執行 smoke test / health verification
8. 依結果進入 success / hold / rollback

## Shared Gate Mapping

| Gate | Typical Checks | Failure Outcome |
|---|---|---|
| Source Gate | lint, unit test, artifact metadata | block / hold |
| Security Gate | secret scanning, SAST, filesystem or dependency scan | block / hold |
| Post-Deploy Health Gate | endpoint health, smoke test, readiness verification | hold / rollback / fallback |

## Apply Workflow
1. 開發者或 CI 觸發 pipeline
2. source gate 與 security gate 通過
3. pipeline 產出 artifact
4. 將 artifact 與 metadata 提交給 release control plane
5. 依環境策略決定是否進入 deployment workflow
6. deploy 完成後執行 post-deploy health gate

## Jenkins Integration Notes
- Jenkins pipeline 採 declarative pipeline 形式，便於閱讀與治理
- credential 應透過 Jenkins Credentials 管理，不要硬寫進 Jenkinsfile
- agent 可以是 static node、Docker agent 或 Kubernetes agent
- deploy gate 可用 `input` step、RBAC 與 folder/job permission 控制
- 共用 health / source / security gate 可參考 `06-DevTools/automation/SHARED-GATE-FRAMEWORK.md` 與對應 example config，將 lint/test/security scan 與 post-deploy health check 納入同一套治理語言

## Slack / Jira Notification Skeleton

預設事件：
- `build_failure`
- `deploy_gate`
- `deploy_success`
- `deploy_failure`

預設行為：
- Slack：發送 channel 通知
- Jira：以 `JIRA_TICKET` 參數做 ticket 關聯，先保留 comment placeholder
- Jira transition 預設不啟用，避免誤動正式工作流

## Notification Event Mapping

| Event | Slack | Jira | Trigger Point |
|---|---|---|---|
| `build_failure` | 發送失敗通知 | comment placeholder | `post { failure }` |
| `deploy_gate` | 發送等待核准通知 | comment placeholder | `Deploy Gate` stage |
| `deploy_success` | 發送成功通知 | comment placeholder | `post { success }` with deploy |
| `deploy_failure` | 與 build failure 共用失敗通知 | comment placeholder | `post { failure }` during deploy |

## Credential Boundaries
- `slack-webhook`: Jenkins credential placeholder，用於 Slack plugin 或 incoming webhook
- `jira-api-token`: Jenkins credential placeholder，用於 Jira API comment/transition
- `JIRA_TICKET`: pipeline parameter，不把 ticket 編號硬寫進 Jenkinsfile

## Jenkins RACI

| Activity | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|
| 維護 Jenkinsfile 與 pipeline 參數 | DevOps / Platform Engineer | CI/CD Owner | App Team, Security | Stakeholders |
| 管理 Jenkins credentials / agent | DevOps / Platform Engineer | Platform Owner | Security | Stakeholders |
| 核准 deploy gate | Service Owner / Release Manager | Service Owner | DevOps, QA | Stakeholders |
| 維護 Slack / Jira notification 規則 | DevOps / Platform Engineer | CI/CD Owner | Service Owner, Security | Stakeholders |
| 維護 source/security/health gate 規則 | DevOps / Platform Engineer | CI/CD Owner | Security, Service Owner | Stakeholders |

## Notes
- 請依實際專案替換 runtime、安裝方式、lint/test/build 指令
- deploy 階段預設只保留 gate / placeholder
- 真實 secrets、runner 與 registry 設定不放在此 skeleton 中
- 若要接真實 Slack/Jira API，建議先在測試 job 驗證訊息格式與權限
