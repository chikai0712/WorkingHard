# CI/CD Practical Skeleton

此目錄提供可套用模板層級的 CI/CD 範例。

## Files
- `.env.example`: local skeleton configuration
- `pipeline.sh`: local helper / metadata viewer
- `github-actions-example.yml`: GitHub Actions pipeline template
- `gitlab-ci-example.yml`: GitLab CI pipeline template

## Included stages
- lint
- test
- build
- artifact upload/package
- deploy gate

## Design Principles

### Build 與 Deploy Gate 分離
這裡把 `lint / test / build / artifact` 放在同一條驗證鏈，但把 deploy 保留成 gate。原因是建置成功不等於適合部署，正式環境通常還需要人工核准、change window、smoke test 或風險確認。

### Pipeline 是驗證層，不是業務邏輯層
CI/CD 應負責驗證與交付，不應在 workflow 內硬編太多業務判斷。這樣做可以降低 pipeline 與應用本身耦合，讓同一套模板可複用到不同專案。

### Artifact 優先
這個目錄假設「可重複部署的交付物」比「每次臨時重新建置」更重要。先產出 artifact，再交給 release/deploy 決策層，可以讓 rollback、追版本與稽核更簡單。

## Typical Flow
1. Checkout 原始碼
2. 安裝依賴
3. 執行 lint / test
4. 建立 artifact
5. 上傳 artifact 或 package metadata
6. 進入 deploy gate

## Sequence Flow
1. 開發者提交變更
2. CI provider 啟動 pipeline
3. Pipeline 執行 lint / test / build
4. 產生 artifact 並保存 metadata
5. 若條件符合，進入 deploy gate
6. 後續交由 release / deployment control plane 決定是否推進

## Decision Matrix
- lint/test 失敗：停止流程，不進入 build / deploy gate
- build 成功但 artifact 不完整：標記失敗，不允許後續 release
- artifact 成功但風險資訊不足：進入 hold / manual review
- 所有驗證通過：交給 release 層決定是否推進

## Apply Workflow
1. 開發者或 CI 觸發 pipeline
2. pipeline 完成驗證並產出 artifact
3. 將 artifact 與 metadata 提交給 release control plane
4. 依環境策略決定是否進入 deployment workflow

## Notes
- 請依實際專案替換 runtime、安裝方式、lint/test/build 指令
- deploy 階段預設只保留 gate / placeholder
- 真實 secrets、runner 與 registry 設定不放在此 skeleton 中
