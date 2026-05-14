# Rollback Guidelines

- 優先定義 migration 是否可逆
- 若不可逆，需先準備 restore plan
- 回滾前確認應用程式版本相容性
- 回滾後重新執行 post-check 與 smoke test
