# Ansible Network Automation Skeleton

這一層負責 FortiGate、Cisco、F5 的設備一致化與 check-only 自動化骨架。

## 目標

- 將設備名稱與管理 IP 變成可後續填寫的變數
- 區分 `FortiGate FW`、`Cisco Core`、`Cisco L2/L3`、`F5 內網 LB`、`F5 外網 LB`
- 使用 Ansible 先做 `check-only`，不直接下配置

## 目錄

```text
ansible/
  ansible.cfg
  inventory/
    dev/
    prod/
  playbooks/
  roles/
    common/
    fortigate_check/
    cisco_check/
    f5_check/
```

## 連線模型

- FortiGate：`httpapi`
- Cisco：`network_cli`
- F5：`httpapi`

認證欄位先放在 `group_vars/` 佔位，後續可改成 `ansible-vault` 或外部 secret 管理。

## Architecture Principles

### Vendor adapter 思維
不同設備的 facts、介面名稱、配置模型不同，因此用 `roles/fortigate_check`、`roles/cisco_check`、`roles/f5_check` 分開，是在建立 vendor adapter 邊界。

### Inventory 是拓樸與責任邊界
`inventory` 不只是主機清單，也是實際環境的分層描述。dev / prod 分離、內外網 LB 分離，都是為了讓檢查結果能映射回真實責任範圍。

### Check summary producer 是 AI 導入橋接層
與其讓 AI 直接解讀大量 facts 或設備回應，先由 `generate_ansible_summary.py` 將 check-only 的結果摘要化，更容易與 recommendation contract、metadata filter 與審批邊界對齊。

### Check-only 先行，避免直接改網
網路設備與 LB 變更風險高，因此這裡先以標準化欄位輸出、facts 收集與一致化檢查為主，再逐步往 compliance / drift remediation 推進。

## 原則

- 第一版只做檢查，不做變更
- 名稱與 IP 以 inventory / vars 管理
- 內外網 LB 分開建模
- 後續再逐步加入 config compliance / drift detection
