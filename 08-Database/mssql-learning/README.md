# MSSQL 學習專案

## 快速開始

### 前置需求
- Docker Desktop（已安裝並執行中）
- [Azure Data Studio](https://aka.ms/azuredatastudio) 或 [DBeaver](https://dbeaver.io/)（GUI 工具）

### 1. 啟動 SQL Server

```bash
cd /Users/ckchiu/Desktop/Project/08-Database/mssql-learning/docker
docker compose up -d
```

### 2. 確認容器狀態

```bash
docker ps | grep mssql-learning
```

### 3. 連線資訊

| 項目 | 值 |
|------|----|
| Host | `localhost` |
| Port | `1433` |
| 帳號 | `SA` |
| 密碼 | `Learn@MSSQL2024` |

### 4. 初始化練習資料庫

開啟 Azure Data Studio 連線後，執行：
```
queries/00-init.sql
```

---

## 目錄結構

```
mssql-learning/
├── docker/
│   ├── docker-compose.yml   # SQL Server 容器設定
│   └── connect.sh           # 快速進入 sqlcmd
├── queries/
│   └── 00-init.sql          # 初始化練習資料庫
├── exercises/               # 練習題（依章節）
├── notes/
│   └── 學習路線圖.md          # 6 週學習計畫
└── README.md
```

---

## 下一步

1. 安裝 Docker Desktop 並啟動
2. 安裝 [Azure Data Studio](https://aka.ms/azuredatastudio)
3. 執行 `docker compose up -d`
4. 依照 `notes/學習路線圖.md` 開始學習
