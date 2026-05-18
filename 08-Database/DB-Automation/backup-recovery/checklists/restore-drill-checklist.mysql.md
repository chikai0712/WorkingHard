# MySQL Restore Drill Checklist

## Before Drill
- 確認目標 MySQL instance、schema 與對應 backup timestamp
- 確認 logical dump 或實體備份檔存在且 checksum 可取得
- 若使用 binlog point-in-time recovery，確認 binlog chain 與 recovery target 已定義
- 確認 restore 僅在隔離環境進行

## During Drill
- 記錄 mysql restore / import 開始時間
- 記錄 restore 完成時間
- 驗證主要 schema、table count 與必要索引存在
- 執行 smoke query，確認關鍵資料可讀取
- 若有 binlog replay，記錄 replay 截止點與驗證結果

## After Drill
- 記錄實際 RTO / 推估 RPO
- 記錄失敗點、binlog 缺口或權限異常
- 更新 MySQL runbook、SOP 與改善項
