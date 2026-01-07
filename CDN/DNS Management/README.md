# CDN/DNS Management Console

跨平台 Web 管控台，用於集中管理多家 Domain Registrar、DNS 及 CDN 供應商。第一階段聚焦在從 GoDaddy 與 Namecheap 拉取帳號底下的網域並提供統一檢視與管理介面。

## Monorepo 結構

```
CDN/DNS Management/
├── backend/              # FastAPI + SQLAlchemy + Postgres
├── frontend/             # Next.js (React + TypeScript)
├── scripts/              # 批次與同步腳本
├── infrastructure/       # IaC / 部署設定
└── README.md             # 專案說明
```

## 快速開始

1. 建立 `.env` （後端）與 `.env.local`（前端），參考各自的 example 檔案。
2. 啟動 Postgres（預設使用 `docker-compose`）。
3. 啟動後端 API：`cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload`。
4. 啟動前端 Web：`cd frontend && npm install && npm run dev`。

## 目前進度
- [x] 專案骨架與資料夾
- [x] 後端 FastAPI 入口、設定與資料模型草稿
- [x] 前端 Next.js 基礎頁面 + API service
- [x] GoDaddy/Namecheap API client 初版
- [x] 域名同步背景作業
- [x] 測試與監控儀表

## 後續規劃
- 擴充 DNS (Cloudflare/Mlytics/Route53) 與 CDN 管理
- 加入 RBAC、審計 log、Webhook 告警
- 建立自動化佈署與日誌/監控整合
