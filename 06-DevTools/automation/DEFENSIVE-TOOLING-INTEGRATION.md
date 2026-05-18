# Defensive Tooling Integration

這份文件說明如何將防禦導向安全工具整合到目前 Git 工作流，而不引入攻擊工具。

## Included Tools
- `gitleaks`: secret scanning
- `semgrep`: SAST / code pattern scanning
- `trivy`: filesystem / dependency vulnerability scanning

## Files
- `.github/workflows/defensive-security-scans.yml`
- `.gitleaks.toml`
- `.semgrep.yml`

## Design Principles

### 防禦優先
這套整合只做防禦用途：
- 找出疑似 secrets
- 找出危險程式碼模式
- 找出高風險依賴或檔案系統弱點

### 先掃描、再治理
掃描工具的角色是提供證據，不是直接做攻擊或滲透。結果應進入 review / remediation / policy gate，而不是變成進攻工具鏈。

### 最小秘密暴露
workflow 預設只使用 GitHub 內建 `GITHUB_TOKEN`，不要求寫入外部真實 secrets。若未來要接 SaaS 版掃描平台，應透過 GitHub Secrets 管理。

## Suggested Workflow
1. 開發者 push 或發 PR
2. GitHub Actions 執行 gitleaks / semgrep / trivy
3. 發現結果後由平台/安全/服務 owner review
4. 視嚴重度決定修正、例外或阻擋 merge

## Guardrails
- 不加入攻擊工具或 exploit framework
- 不把真實 token / key / credentials 寫入設定檔
- 對誤報應以 allowlist / rule tuning 處理，不直接關閉整個掃描層
