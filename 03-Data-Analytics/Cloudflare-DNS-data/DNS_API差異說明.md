# Cloudflare API 差異說明

## 問題分析

在腳本中使用了兩個不同的 Cloudflare API，它們對 Free Plan 的限制是不同的：

### 1. HTTP Analytics API (GraphQL)
- **API 端點**: `https://api.cloudflare.com/client/v4/graphql`
- **查詢類型**: `httpRequests1dGroups`
- **Free Plan 限制**: **可以查詢過去 7 天的資料**
- **使用場景**: 獲取 HTTP 相關指標（總流量、總請求數、緩存流量、緩存請求數）
- **代碼位置**: `get_zone_metric()` 函數（第 262-391 行）

### 2. DNS Analytics API - GraphQL（優先使用）
- **API 端點**: `https://api.cloudflare.com/client/v4/graphql`
- **查詢類型**: `dnsAnalyticsAdaptiveGroups`
- **Free Plan 限制**: **可以查詢過去 7 天的資料**（與 HTTP Analytics 一致）
- **使用場景**: 獲取 DNS 查詢數（queryCount）
- **代碼位置**: `get_dns_query_count()` 函數中的 `_get_dns_queries_graphql()`（優先使用）

### 3. DNS Analytics API - REST（備用方案）
- **API 端點**: `https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_analytics/report`
- **查詢類型**: DNS 查詢統計
- **Free Plan 限制**: **只能查詢過去 6 小時的資料**（Cloudflare 官方限制）
- **使用場景**: 當 GraphQL API 失敗時，作為備用方案獲取 DNS 查詢數
- **代碼位置**: `get_dns_query_count()` 函數中的 `_get_dns_queries_rest()`（備用）

## 為什麼會有這個差異？

這是 Cloudflare 根據不同功能制定的計劃限制：

1. **HTTP Analytics**: 
   - Free Plan 可以查看過去 7 天的 HTTP 流量和請求數據
   - 這是基本的網站分析功能，即使是免費計劃也提供較長時間的歷史數據

2. **DNS Analytics**:
   - Free Plan 只能查看過去 6 小時的 DNS 查詢數據
   - DNS 分析被視為更進階的功能，免費計劃僅提供短時間的數據
   - 這是 Cloudflare 官方 API 的限制，不是腳本的問題

## 實際資料驗證

查看 CSV 檔案可以發現：
- Free Plan 的域名有完整的 HTTP 指標數據（總請求數、總流量等，涵蓋 7 天）
- 但 DNS查詢數 欄位顯示為 `0` 或 `N/A (計劃限制)`

這是因為：
1. 腳本嘗試查詢 DNS Analytics 時，由於 Free Plan 的 6 小時限制，可能：
   - 返回 0（如果 API 允許查詢但沒有數據）
   - 返回 "N/A (計劃限制)"（如果 API 明確拒絕超過 6 小時的查詢）

## 解決方案

如果需要 Free Plan 的 DNS 查詢數據：

1. **升級計劃**: 
   - Pro Plan ($20/月) 可以查詢 24 小時的 DNS 數據
   - Business Plan 可以查詢 30 天的 DNS 數據

2. **使用 Cloudflare Dashboard**:
   - 雖然 API 限制 6 小時，但 Dashboard 可能顯示更長時間的數據
   - 但這無法通過 API 獲取

3. **調整查詢時間範圍**:
   - 對於 Free Plan，腳本已經自動調整為只查詢 6 小時（`get_dns_time_window` 函數）
   - 如果仍返回錯誤，可能是計劃完全不支援 DNS Analytics API

## 代碼邏輯確認

在 `get_dns_time_window()` 函數中（第 51-95 行）：
- Free Plan: 設定為 6 小時 (`time_range_desc = "6H"`)
- Pro Plan: 設定為 24 小時 (`time_range_desc = "24H"`)
- Business/Enterprise: 設定為 30 天 (`time_range_desc = "30D"`)

這個邏輯是正確的，符合 Cloudflare API 的限制。

## 更新說明（重要）

腳本已更新為**優先使用 GraphQL API** 來獲取 DNS 查詢數據：

1. **優先使用 GraphQL API (`dnsAnalyticsAdaptiveGroups`)**：
   - Free Plan 可以查詢 **7 天**的 DNS 查詢數據
   - 與 HTTP Analytics 使用相同的 GraphQL 端點
   - 這是為什麼 `cloudflare_data` 檔案中可以看到 Free Plan 的 7 天 DNS 數據

2. **備用 REST API**：
   - 如果 GraphQL API 失敗，才會使用 REST API
   - REST API 對 Free Plan 的限制仍然是 6 小時

## 結論

**更新後**：Free Plan 現在可以通過 GraphQL API 獲取 **7 天的 DNS 查詢數據**，與 HTTP Analytics 的時間範圍一致。

如果 GraphQL API 不可用或失敗，腳本會自動回退到 REST API（6 小時限制）。

