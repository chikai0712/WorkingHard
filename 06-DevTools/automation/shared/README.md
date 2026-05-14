# Shared Automation Utilities

這裡放跨專案共用的 shell / Python helper skeleton。

## Suggested contents
- env loader
- logging helper
- timestamped report writer
- retry wrapper

## Design Principles

### Shared utilities 只放共通能力
共用層應只承載通用功能，例如：讀設定、重試、記錄、報表輸出。不應把專案特定邏輯放進 shared，否則所有專案都會被迫跟著耦合。

### 小而穩定
shared 層一旦被多個專案引用，變更成本會很高，因此這一層應保持 API 小、依賴少、行為穩定。

### 工具層不決定策略
shared 可以提供 `retry` 或 `report_writer`，但不應決定什麼時候該 retry、報表該長什麼樣。策略應留在上層模組。
