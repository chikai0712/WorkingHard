package metrics

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

var (
	// HTTP 請求指標
	HTTPRequestsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "http_requests_total",
			Help: "HTTP 請求總數",
		},
		[]string{"method", "endpoint", "status"},
	)

	HTTPRequestDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "http_request_duration_seconds",
			Help:    "HTTP 請求處理時間",
			Buckets: prometheus.DefBuckets,
		},
		[]string{"method", "endpoint"},
	)

	// 注單處理指標
	OrderProcessedTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "order_processed_total",
			Help: "處理的注單總數",
		},
		[]string{"status"}, // success, failed
	)

	OrderProcessingDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "order_processing_duration_seconds",
			Help:    "注單處理時間",
			Buckets: []float64{0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10},
		},
		[]string{"operation"}, // create, update, query
	)

	// Goroutine 指標
	GoroutineCount = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "goroutine_count",
			Help: "當前 Goroutine 數量",
		},
	)

	// 數據庫連接池指標
	DBConnectionsActive = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "db_connections_active",
			Help: "活躍的數據庫連接數",
		},
	)

	DBConnectionsIdle = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "db_connections_idle",
			Help: "空閒的數據庫連接數",
		},
	)

	// Redis 指標
	RedisOperationsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "redis_operations_total",
			Help: "Redis 操作總數",
		},
		[]string{"operation", "status"}, // get, set, del, success, failed
	)

	RedisOperationDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "redis_operation_duration_seconds",
			Help:    "Redis 操作時間",
			Buckets: []float64{0.0001, 0.0005, 0.001, 0.005, 0.01, 0.025, 0.05, 0.1},
		},
		[]string{"operation"},
	)

	// Kafka 指標
	KafkaMessagesProduced = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "kafka_messages_produced_total",
			Help: "Kafka 生產的消息總數",
		},
		[]string{"topic", "status"},
	)

	KafkaMessagesConsumed = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "kafka_messages_consumed_total",
			Help: "Kafka 消費的消息總數",
		},
		[]string{"topic", "status"},
	)
)

