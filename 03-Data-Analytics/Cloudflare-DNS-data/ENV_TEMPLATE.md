# Cloudflare 環境變數範本

將此檔內容複製為 `.env` 或直接 export，並填入自己的值（不要提交真實金鑰）。

## 方案一：API Token（推薦，可多組）
```bash
export CF_ACCOUNTS_JSON='[
  {"api_token":"<TOKEN_A>","account_id":"<ACCOUNT_A>","email":"a@example.com"},
  {"api_token":"<TOKEN_B>","account_id":"<ACCOUNT_B>","email":"b@example.com"},
  {"api_token":"<TOKEN_C>","account_id":"<ACCOUNT_C>","email":"c@example.com"}
]'
```

## 方案二：暫時相容舊 Global API Key（不建議長期使用）
```bash
export CF_ACCOUNTS_JSON='[
  {"api_key":"<GLOBAL_API_KEY>","email":"user@example.com","account_id":"<ACCOUNT_ID>"},
  {"api_key":"<GLOBAL_API_KEY_2>","email":"user2@example.com","account_id":"<ACCOUNT_ID_2>"}
]'
```

## 其他可選變數（cloudflare_dns_query_count.py）
```bash
export CF_API_TOKEN="<YOUR_API_TOKEN>"    # 若只跑 query_count 腳本，可直接用這變數
export CF_ACCOUNT_ID="<ACCOUNT_ID>"       # 可選，限定帳戶
export CF_ZONES="example.com,foo.com"     # 可選，限定特定網域
```

> 建議：盡快改用 API Token（最小權限：Zone:Read + DNS Analytics:Read），並旋轉/停用舊的 Global API Key。

