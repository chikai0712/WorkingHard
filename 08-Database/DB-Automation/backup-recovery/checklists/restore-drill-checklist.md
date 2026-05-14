# Restore Drill Checklist

## Before Drill
- 確認演練目標資料庫與時間點
- 確認備份檔存在、大小合理、checksum 可取得
- 確認使用的是非正式環境或隔離演練環境

## During Drill
- 記錄 restore 開始時間
- 記錄 restore 完成時間
- 驗證 schema / table count / key queries
- 驗證應用程式必要資料是否存在

## After Drill
- 記錄實際 RTO / 推估 RPO
- 記錄失敗點與改進項
- 更新 runbook / SOP / 週報
