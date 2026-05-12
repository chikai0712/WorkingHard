# Backend (FastAPI)

提供 API，統一串接 GoDaddy 與 Namecheap，並將結果寫入 PostgreSQL。

## 結構
```
backend/
├── app/
│   ├── api/
│   │   └── routes/
│   │       └── domains.py
│   ├── core/        # 設定、安控、依賴注入
│   ├── db/          # Session 與初始化
│   ├── models/      # SQLAlchemy models
│   ├── schemas/     # Pydantic schema
│   └── services/    # Provider client & domain service
├── scripts/
├── tests/
└── requirements.txt
```

## 設定
- 建立 `.env`（可複製 `env.example` 後更名）並填入 Postgres URL、加密用 `SECRET_KEY` 與第三方 API key。
- Alembic migration 會以 `app/models` 為來源。
- 若需背景同步，啟動 API 時會自動載入 APScheduler，亦可獨立執行 `app/workers/sync_runner.py`。

## 常用指令
```
# 安裝依賴
pip install -r requirements.txt

# 啟動 API
uvicorn app.main:app --reload

# 產生資料庫
alembic upgrade head
```

## API 範例
- `GET /healthz`：健康檢查
- `POST /accounts`：建立供應商帳號
- `GET /providers/{provider_id}/domains`：拉取指定帳號的網域列表

更多細節請參考 `app/api/routes`。
