# Configuration Management Skeleton

放 Ansible / shell bootstrap / inventory template。

第一版只提供：
- inventory example
- dry-run command example
- config drift 檢查入口

## Design Principles

### Config 與 Provisioning 分離
IaC 偏向「建資源」，Configuration Management 偏向「讓既有資源保持一致」。這裡保留獨立目錄，是為了把主機/節點/設備上的配置管理與雲資源生命週期分開。

### Drift detection 優先於直接修正
在大型環境裡，直接改配置很容易覆蓋現場例外或臨時修補，因此第一版先偏向 `--check` / `--diff` / drift detection。先看差異，再決定是否修正，比直接套版安全。

### Inventory 是控制面，不是秘密儲存區
inventory 應描述目標與分組，不應承載真實憑證。正式認證資訊建議放在 vault 或外部 secret system。
