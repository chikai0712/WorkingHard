.PHONY: build run test clean docker-build docker-up docker-down

# 構建所有服務
build:
	@echo "構建 Order Service..."
	@cd cmd/order-service && go build -o ../../bin/order-service
	@echo "構建 Gateway..."
	@cd cmd/gateway && go build -o ../../bin/gateway

# 運行服務
run-order:
	@cd cmd/order-service && go run main.go

run-gateway:
	@cd cmd/gateway && go run main.go

# 測試
test:
	@go test ./... -v

# 清理
clean:
	@rm -rf bin/
	@go clean

# Docker 構建
docker-build:
	@docker build -t betting-service/order-service:latest -f deploy/docker/Dockerfile.order-service .
	@docker build -t betting-service/gateway:latest -f deploy/docker/Dockerfile.gateway .

# Docker Compose
docker-up:
	@docker-compose -f deploy/docker/docker-compose.yml up -d

docker-down:
	@docker-compose -f deploy/docker/docker-compose.yml down

# 初始化數據庫
init-db:
	@psql -U postgres -f scripts/init_db.sql

