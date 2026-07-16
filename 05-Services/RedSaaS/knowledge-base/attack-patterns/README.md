# 博弈平台攻擊模式知識庫

> 這個目錄記錄博弈平台最常見的漏洞模式。
> 每個漏洞類型對應一個 Markdown 文件，文件內容來自靶場驗證結果和公開 Bug Bounty 報告。
> 這是 Template 庫的知識來源，也是報告自動生成器的訓練素材。

## 索引

| 漏洞類型 | 嚴重度 | Template | 驗證狀態 |
|---------|--------|----------|---------|
| 玩家餘額 IDOR | 高 | `gambling/idor-player-balance.yaml` | 🔲 未驗證 |
| 代理商後台 Rate Limit 缺失 | 中 | `gambling/agent-panel-no-ratelimit.yaml` | 🔲 未驗證 |
| 存提款金額邊界驗證缺失 | 嚴重 | `gambling/withdrawal-amount-boundary.yaml` | 🔲 未驗證 |
| 玩家 Token 洩漏 | 高 | 待建立 | 🔲 未建立 |
| 後台管理介面預設路徑暴露 | 中 | 待建立 | 🔲 未建立 |

## 驗證狀態說明

- 🔲 未驗證 / 未建立
- 🔄 靶場測試中
- ✅ 靶場驗證通過（TP 率 > 80%，FP 率 < 10%）
- ⚠️ 需要調整（FP 率過高或有遺漏）
