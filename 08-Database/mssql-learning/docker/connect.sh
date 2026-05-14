#!/bin/bash
# 快速連入 MSSQL 容器的 sqlcmd
echo "連線到 MSSQL (SA 帳號)..."
docker exec -it mssql-learning \
  /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U SA -P 'Learn@MSSQL2024' -No
