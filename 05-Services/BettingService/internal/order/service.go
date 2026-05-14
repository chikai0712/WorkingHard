package order

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"time"

	"github.com/chikai0712/betting-service/internal/common"
	"github.com/chikai0712/betting-service/pkg/config"
	"github.com/chikai0712/betting-service/pkg/logger"
	"github.com/chikai0712/betting-service/pkg/metrics"
	"github.com/gin-gonic/gin"
	"github.com/go-redis/redis/v8"
	"github.com/lib/pq"
	"github.com/segmentio/kafka-go"
	"go.uber.org/zap"
)

type OrderService struct {
	db          *sql.DB
	redisClient *redis.Client
	kafkaWriter *kafka.Writer
	goroutinePool *common.GoroutinePool
	rateLimiter   *common.RateLimiter
	config        *config.Config
}

func NewOrderService(cfg *config.Config) (*OrderService, error) {
	// 初始化數據庫連接
	db, err := initDB(cfg)
	if err != nil {
		return nil, fmt.Errorf("初始化數據庫失敗: %w", err)
	}

	// 初始化 Redis
	redisClient := redis.NewClient(&redis.Options{
		Addr:         fmt.Sprintf("%s:%d", cfg.Redis.Host, cfg.Redis.Port),
		Password:     cfg.Redis.Password,
		DB:           cfg.Redis.DB,
		PoolSize:     cfg.Redis.PoolSize,
		MinIdleConns: cfg.Redis.MinIdleConns,
	})

	// 測試 Redis 連接
	ctx := context.Background()
	if err := redisClient.Ping(ctx).Err(); err != nil {
		return nil, fmt.Errorf("Redis 連接失敗: %w", err)
	}

	// 初始化 Kafka Writer
	kafkaWriter := &kafka.Writer{
		Addr:         kafka.TCP(cfg.Kafka.Brokers...),
		Topic:        cfg.Kafka.Topic,
		Balancer:     &kafka.LeastBytes{},
		BatchSize:    cfg.Kafka.BatchSize,
		BatchTimeout: time.Duration(cfg.Kafka.BatchTimeout) * time.Millisecond,
		Async:        true, // 異步寫入提升性能
	}

	// 創建 Goroutine Pool（1000 workers, 10000 queue size）
	goroutinePool := common.NewGoroutinePool(1000, 10000)

	// 創建限流器（每秒 10000 請求）
	rateLimiter := common.NewRateLimiter(10000, 10000)

	service := &OrderService{
		db:            db,
		redisClient:   redisClient,
		kafkaWriter:   kafkaWriter,
		goroutinePool: goroutinePool,
		rateLimiter:   rateLimiter,
		config:        cfg,
	}

	return service, nil
}

func initDB(cfg *config.Config) (*sql.DB, error) {
	dsn := fmt.Sprintf("host=%s port=%d user=%s password=%s dbname=%s sslmode=disable",
		cfg.Database.Host, cfg.Database.Port, cfg.Database.User, cfg.Database.Password, cfg.Database.DBName)

	db, err := sql.Open("postgres", dsn)
	if err != nil {
		return nil, err
	}

	db.SetMaxOpenConns(cfg.Database.MaxOpenConns)
	db.SetMaxIdleConns(cfg.Database.MaxIdleConns)
	db.SetConnMaxLifetime(time.Duration(cfg.Database.ConnMaxLifetime) * time.Second)

	if err := db.Ping(); err != nil {
		return nil, err
	}

	return db, nil
}

// CreateOrder 創建注單
func (s *OrderService) CreateOrder(c *gin.Context) {
	start := time.Now()

	// 限流檢查
	if !s.rateLimiter.Allow() {
		metrics.OrderProcessedTotal.WithLabelValues("rate_limited").Inc()
		c.JSON(429, gin.H{"error": "請求過於頻繁，請稍後再試"})
		return
	}

	var req OrderRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}

	// 使用 Goroutine Pool 異步處理
	done := make(chan error, 1)
	s.goroutinePool.Submit(func() {
		err := s.processOrder(c.Request.Context(), &req)
		done <- err
	})

	// 等待處理結果（設置超時）
	select {
	case err := <-done:
		if err != nil {
			metrics.OrderProcessedTotal.WithLabelValues("failed").Inc()
			logger.Logger.Error("創建注單失敗", zap.Error(err), zap.String("order_no", req.OrderNo))
			c.JSON(500, gin.H{"error": "創建注單失敗"})
			return
		}
		metrics.OrderProcessedTotal.WithLabelValues("success").Inc()
		duration := time.Since(start).Seconds()
		metrics.OrderProcessingDuration.WithLabelValues("create").Observe(duration)
		c.JSON(200, gin.H{"message": "注單創建成功", "order_no": req.OrderNo})
	case <-time.After(5 * time.Second):
		metrics.OrderProcessedTotal.WithLabelValues("timeout").Inc()
		c.JSON(504, gin.H{"error": "請求超時"})
	}
}

// processOrder 處理注單（內部方法）
func (s *OrderService) processOrder(ctx context.Context, req *OrderRequest) error {
	// 1. 檢查 Redis 緩存（防止重複提交）
	cacheKey := fmt.Sprintf("order:lock:%s", req.OrderNo)
	exists, err := s.redisClient.Exists(ctx, cacheKey).Result()
	if err != nil {
		return fmt.Errorf("Redis 檢查失敗: %w", err)
	}
	if exists > 0 {
		return fmt.Errorf("注單號已存在")
	}

	// 2. 設置 Redis 鎖（5 秒過期）
	if err := s.redisClient.SetNX(ctx, cacheKey, "1", 5*time.Second).Err(); err != nil {
		return fmt.Errorf("設置 Redis 鎖失敗: %w", err)
	}

	// 3. 寫入數據庫
	order := &Order{
		UserID:    req.UserID,
		OrderNo:   req.OrderNo,
		GameType:  req.GameType,
		BetAmount: req.BetAmount,
		Status:    "pending",
		BetTime:   time.Now(),
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	query := `INSERT INTO orders (user_id, order_no, game_type, bet_amount, status, bet_time, created_at, updated_at)
			  VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING id`
	
	err = s.db.QueryRowContext(ctx, query,
		order.UserID, order.OrderNo, order.GameType, order.BetAmount,
		order.Status, order.BetTime, order.CreatedAt, order.UpdatedAt,
	).Scan(&order.ID)
	
	if err != nil {
		// 檢查是否為重複鍵錯誤
		if pqErr, ok := err.(*pq.Error); ok && pqErr.Code == "23505" {
			return fmt.Errorf("注單號已存在")
		}
		return fmt.Errorf("數據庫插入失敗: %w", err)
	}

	// 4. 寫入 Redis 緩存（熱點數據）
	orderKey := fmt.Sprintf("order:%s", req.OrderNo)
	orderJSON, _ := json.Marshal(order)
	s.redisClient.Set(ctx, orderKey, orderJSON, 1*time.Hour)

	// 5. 發送到 Kafka（異步處理）
	message, _ := json.Marshal(map[string]interface{}{
		"order_id":   order.ID,
		"order_no":   order.OrderNo,
		"user_id":    order.UserID,
		"game_type":  order.GameType,
		"bet_amount": order.BetAmount,
		"status":     order.Status,
		"timestamp":  time.Now().Unix(),
	})

	if err := s.kafkaWriter.WriteMessages(ctx, kafka.Message{
		Key:   []byte(req.OrderNo),
		Value: message,
	}); err != nil {
		logger.Logger.Warn("Kafka 發送失敗", zap.Error(err))
		// 不影響主流程，僅記錄日誌
	}

	return nil
}

// GetOrder 查詢注單
func (s *OrderService) GetOrder(c *gin.Context) {
	orderNo := c.Param("order_no")

	// 先查 Redis 緩存
	ctx := c.Request.Context()
	orderKey := fmt.Sprintf("order:%s", orderNo)
	cached, err := s.redisClient.Get(ctx, orderKey).Result()
	if err == nil {
		var order Order
		if json.Unmarshal([]byte(cached), &order) == nil {
			c.JSON(200, order)
			return
		}
	}

	// 查詢數據庫
	query := `SELECT id, user_id, order_no, game_type, bet_amount, win_amount, status, bet_time, settle_time, created_at, updated_at
			  FROM orders WHERE order_no = $1`
	
	var order Order
	err = s.db.QueryRowContext(ctx, query, orderNo).Scan(
		&order.ID, &order.UserID, &order.OrderNo, &order.GameType,
		&order.BetAmount, &order.WinAmount, &order.Status,
		&order.BetTime, &order.SettleTime, &order.CreatedAt, &order.UpdatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			c.JSON(404, gin.H{"error": "注單不存在"})
			return
		}
		c.JSON(500, gin.H{"error": "查詢失敗"})
		return
	}

	// 更新緩存
	orderJSON, _ := json.Marshal(order)
	s.redisClient.Set(ctx, orderKey, orderJSON, 1*time.Hour)

	c.JSON(200, order)
}

// ListOrders 查詢注單列表
func (s *OrderService) ListOrders(c *gin.Context) {
	var req OrderQueryRequest
	if err := c.ShouldBindQuery(&req); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}

	// 構建查詢條件
	where := "1=1"
	args := []interface{}{}
	argIndex := 1

	if req.UserID != nil {
		where += fmt.Sprintf(" AND user_id = $%d", argIndex)
		args = append(args, *req.UserID)
		argIndex++
	}
	if req.OrderNo != nil {
		where += fmt.Sprintf(" AND order_no = $%d", argIndex)
		args = append(args, *req.OrderNo)
		argIndex++
	}
	if req.Status != nil {
		where += fmt.Sprintf(" AND status = $%d", argIndex)
		args = append(args, *req.Status)
		argIndex++
	}
	if req.StartTime != nil {
		where += fmt.Sprintf(" AND bet_time >= $%d", argIndex)
		args = append(args, *req.StartTime)
		argIndex++
	}
	if req.EndTime != nil {
		where += fmt.Sprintf(" AND bet_time <= $%d", argIndex)
		args = append(args, *req.EndTime)
		argIndex++
	}

	// 分頁
	offset := (req.Page - 1) * req.PageSize
	args = append(args, req.PageSize, offset)

	// 查詢總數
	countQuery := fmt.Sprintf("SELECT COUNT(*) FROM orders WHERE %s", where)
	var total int64
	if err := s.db.QueryRowContext(c.Request.Context(), countQuery, args[:len(args)-2]...).Scan(&total); err != nil {
		c.JSON(500, gin.H{"error": "查詢失敗"})
		return
	}

	// 查詢列表
	listQuery := fmt.Sprintf(`
		SELECT id, user_id, order_no, game_type, bet_amount, win_amount, status, bet_time, settle_time, created_at, updated_at
		FROM orders WHERE %s ORDER BY created_at DESC LIMIT $%d OFFSET $%d
	`, where, argIndex, argIndex+1)

	rows, err := s.db.QueryContext(c.Request.Context(), listQuery, args...)
	if err != nil {
		c.JSON(500, gin.H{"error": "查詢失敗"})
		return
	}
	defer rows.Close()

	var orders []OrderResponse
	for rows.Next() {
		var order Order
		if err := rows.Scan(
			&order.ID, &order.UserID, &order.OrderNo, &order.GameType,
			&order.BetAmount, &order.WinAmount, &order.Status,
			&order.BetTime, &order.SettleTime, &order.CreatedAt, &order.UpdatedAt,
		); err != nil {
			continue
		}
		orders = append(orders, OrderResponse{
			ID:        order.ID,
			OrderNo:   order.OrderNo,
			Status:    order.Status,
			BetAmount: order.BetAmount,
			CreatedAt: order.CreatedAt,
		})
	}

	c.JSON(200, OrderListResponse{
		Orders:   orders,
		Total:    total,
		Page:     req.Page,
		PageSize: req.PageSize,
	})
}

// SettleOrder 結算注單
func (s *OrderService) SettleOrder(c *gin.Context) {
	orderNo := c.Param("order_no")

	var req struct {
		WinAmount float64 `json:"win_amount" binding:"required"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}

	// 更新數據庫
	query := `UPDATE orders SET win_amount = $1, status = 'settled', settle_time = $2, updated_at = $3
			  WHERE order_no = $4 AND status = 'pending' RETURNING id`
	
	var orderID int64
	err := s.db.QueryRowContext(c.Request.Context(), query,
		req.WinAmount, time.Now(), time.Now(), orderNo,
	).Scan(&orderID)

	if err != nil {
		if err == sql.ErrNoRows {
			c.JSON(404, gin.H{"error": "注單不存在或已結算"})
			return
		}
		c.JSON(500, gin.H{"error": "結算失敗"})
		return
	}

	// 清除緩存
	orderKey := fmt.Sprintf("order:%s", orderNo)
	s.redisClient.Del(c.Request.Context(), orderKey)

	c.JSON(200, gin.H{"message": "結算成功", "order_no": orderNo})
}

// Close 關閉服務
func (s *OrderService) Close() {
	if s.db != nil {
		s.db.Close()
	}
	if s.redisClient != nil {
		s.redisClient.Close()
	}
	if s.kafkaWriter != nil {
		s.kafkaWriter.Close()
	}
	if s.goroutinePool != nil {
		s.goroutinePool.Shutdown()
	}
}

