package main

import (
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/chikai0712/betting-service/internal/common"
	"github.com/chikai0712/betting-service/internal/gateway"
	"github.com/chikai0712/betting-service/pkg/config"
	"github.com/chikai0712/betting-service/pkg/logger"
	"github.com/chikai0712/betting-service/pkg/metrics"
	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

func main() {
	// 載入配置
	cfg, err := config.LoadConfig("")
	if err != nil {
		panic(fmt.Sprintf("載入配置失敗: %v", err))
	}

	// 初始化日誌
	if err := logger.InitLogger(cfg.Log.Level, cfg.Log.OutputPath, cfg.Log.MaxSize, cfg.Log.MaxBackups, cfg.Log.MaxAge); err != nil {
		panic(fmt.Sprintf("初始化日誌失敗: %v", err))
	}
	defer logger.Logger.Sync()

	logger.Logger.Info("啟動 API Gateway", zap.Int("port", cfg.Server.Port))

	// 初始化 Gateway
	gatewayService, err := gateway.NewGatewayService(cfg)
	if err != nil {
		logger.Logger.Fatal("初始化 Gateway 失敗", zap.Error(err))
	}
	defer gatewayService.Close()

	// 設置 Gin 模式
	if cfg.Server.Mode == "release" {
		gin.SetMode(gin.ReleaseMode)
	}

	// 創建 HTTP 服務器
	router := gin.New()
	router.Use(gin.Recovery())
	router.Use(metricsMiddleware())
	router.Use(rateLimitMiddleware(gatewayService.GetRateLimiter()))

	// 健康檢查
	router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "ok"})
	})

	// API 路由
	api := router.Group("/api/v1")
	{
		api.Any("/*path", gatewayService.Proxy)
	}

	// 啟動服務器
	srv := &http.Server{
		Addr:           fmt.Sprintf(":%d", cfg.Server.Port),
		Handler:        router,
		ReadTimeout:    time.Duration(cfg.Server.ReadTimeout) * time.Second,
		WriteTimeout:   time.Duration(cfg.Server.WriteTimeout) * time.Second,
		MaxHeaderBytes: 1 << 20,
	}

	// 優雅關閉
	go func() {
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Logger.Fatal("服務器啟動失敗", zap.Error(err))
		}
	}()

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	logger.Logger.Info("正在關閉服務器...")
	// ... 關閉邏輯
}

func metricsMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		c.Next()
		duration := time.Since(start).Seconds()
		status := fmt.Sprintf("%d", c.Writer.Status())
		metrics.HTTPRequestsTotal.WithLabelValues(c.Request.Method, c.FullPath(), status).Inc()
		metrics.HTTPRequestDuration.WithLabelValues(c.Request.Method, c.FullPath()).Observe(duration)
	}
}

func rateLimitMiddleware(limiter *common.RateLimiter) gin.HandlerFunc {
	return func(c *gin.Context) {
		if !limiter.Allow() {
			c.JSON(429, gin.H{"error": "請求過於頻繁"})
			c.Abort()
			return
		}
		c.Next()
	}
}

