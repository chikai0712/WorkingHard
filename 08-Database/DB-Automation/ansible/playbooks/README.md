# Example run

```bash
ansible-playbook -i inventory/dev/hosts.yml playbooks/network_consistency_check.yml
```

## 後續可補

- FortiGate facts / policy / interface checks
- Cisco VLAN / trunk / SVI / routing checks
- F5 virtual server / pool / node / monitor checks
- 匯出成 JSON/CSV report
