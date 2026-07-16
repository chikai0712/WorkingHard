# RedSaaS — 博弈產業資安自動化平台

博弈產業專用的攻擊面管理 + 合規報告自動化平台。
先對內部測試環境使用，累積知識庫後對外銷售。

## 目錄結構

```
RedSaaS/
├── .planning/
│   ├── ROADMAP.md          ← 三階段執行路線圖
│   └── STATE.md            ← 當前進度
├── knowledge-base/
│   └── attack-patterns/    ← 博弈漏洞模式文件庫
├── templates/
│   ├── gambling/           ← 博弈業務邏輯專用 Nuclei templates
│   └── generic/            ← 通用 web 漏洞 templates（待建立）
├── lab/
│   ├── docker/
│   │   └── docker-compose.yml  ← 本地靶場環境（crAPI + DVWA + DefectDojo）
│   └── README.md           ← 靶場操作說明
├── reports/
│   └── samples/            ← 報告範本（待建立）
└── scripts/                ← 自動化輔助腳本（待建立）
```

## 快速開始

```bash
# 啟動本地靶場環境
cd lab/docker
docker compose up -d

# 對 crAPI 跑第一次博弈漏洞掃描
docker compose run --rm nuclei \
  -t /templates/gambling/ \
  -u http://crapi-web \
  -o /output/result.json -json
```

詳細操作見 `lab/README.md`。

## 當前 Templates

| Template | 漏洞類型 | 嚴重度 |
|----------|---------|--------|
| `gambling/idor-player-balance.yaml` | 玩家餘額 IDOR | 高 |
| `gambling/agent-panel-no-ratelimit.yaml` | 代理商後台暴力破解 | 中 |
| `gambling/withdrawal-amount-boundary.yaml` | 存提款金額邊界繞過 | 嚴重 |

## 恢復進度

```
Read 05-Services/RedSaaS/.planning/STATE.md and ROADMAP.md, then tell me current progress.
```
