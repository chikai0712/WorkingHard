# BIND DNS Container Makefile
# 提供便捷的命令來管理 BIND DNS 容器

.PHONY: help start stop restart status logs test clean

help:
	@echo "BIND DNS Container 管理命令"
	@echo ""
	@echo "可用命令:"
	@echo "  make start      - 啟動 BIND DNS 容器"
	@echo "  make stop       - 停止 BIND DNS 容器"
	@echo "  make restart    - 重啟 BIND DNS 容器"
	@echo "  make status     - 查看容器狀態"
	@echo "  make logs       - 查看容器日誌"
	@echo "  make test       - 測試 DNS 服務"
	@echo "  make clean      - 停止並清理容器"
	@echo "  make shell      - 進入容器 shell"
	@echo "  make checkconf  - 檢查配置文件語法"
	@echo ""

start:
	@echo "🚀 啟動 BIND DNS 容器..."
	@docker-compose up -d
	@echo "✅ 容器已啟動"
	@make status

stop:
	@echo "🛑 停止 BIND DNS 容器..."
	@docker-compose down
	@echo "✅ 容器已停止"

restart:
	@echo "🔄 重啟 BIND DNS 容器..."
	@docker-compose restart bind9
	@echo "✅ 容器已重啟"
	@make status

status:
	@echo "📊 容器狀態:"
	@docker-compose ps
	@echo ""
	@if docker ps | grep -q bind9-dns; then \
		echo "✅ BIND DNS 容器運行中"; \
		echo ""; \
		echo "📡 測試 DNS:"; \
		echo "   dig @127.0.0.1 example.com"; \
	else \
		echo "❌ BIND DNS 容器未運行"; \
	fi

logs:
	@echo "📝 查看容器日誌 (Ctrl+C 退出):"
	@docker-compose logs -f bind9

test:
	@echo "🧪 測試 DNS 服務..."
	@if ! docker ps | grep -q bind9-dns; then \
		echo "❌ 錯誤: 容器未運行，請先執行 make start"; \
		exit 1; \
	fi
	@echo "✅ 容器運行中"
	@echo ""
	@echo "📡 測試 example.com:"
	@dig @127.0.0.1 example.com +short 2>/dev/null || echo "⚠️  查詢失敗或未配置"
	@echo ""
	@echo "🌐 測試遞迴查詢 (google.com):"
	@dig @127.0.0.1 google.com +short 2>/dev/null | head -1 || echo "⚠️  查詢失敗"

clean:
	@echo "🧹 清理容器和數據..."
	@read -p "確定要刪除所有數據嗎? (y/N): " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		echo "✅ 清理完成"; \
	else \
		echo "❌ 取消清理"; \
	fi

shell:
	@echo "🐚 進入容器 shell..."
	@docker exec -it bind9-dns bash

checkconf:
	@echo "🔍 檢查配置文件語法..."
	@docker exec -it bind9-dns named-checkconf /etc/bind/named.conf || \
		docker run --rm -v $$(pwd)/bind/config:/etc/bind ubuntu/bind9:latest named-checkconf

