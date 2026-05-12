package gateway

import (
	"fmt"
	"net/http"
	"net/http/httputil"
	"net/url"
	"sync"

	"github.com/chikai0712/betting-service/internal/common"
	"github.com/chikai0712/betting-service/pkg/config"
	"github.com/gin-gonic/gin"
)

type GatewayService struct {
	orderServiceURLs []*url.URL
	currentIndex     int
	mu               sync.Mutex
	proxy            *httputil.ReverseProxy
	rateLimiter      *common.RateLimiter
}

func NewGatewayService(cfg *config.Config) (*GatewayService, error) {
	// 從配置或環境變數讀取後端服務地址
	// 這裡簡化處理，實際應該從服務發現獲取
	serviceURLs := []string{
		"http://order-service:8080",
		"http://order-service-2:8080",
		"http://order-service-3:8080",
	}

	var urls []*url.URL
	for _, u := range serviceURLs {
		parsed, err := url.Parse(u)
		if err != nil {
			return nil, fmt.Errorf("解析 URL 失敗: %w", err)
		}
		urls = append(urls, parsed)
	}

	// 創建限流器（每秒 50000 請求）
	rateLimiter := common.NewRateLimiter(50000, 50000)

	return &GatewayService{
		orderServiceURLs: urls,
		rateLimiter:    rateLimiter,
	}, nil
}

// GetRateLimiter 獲取限流器
func (g *GatewayService) GetRateLimiter() *common.RateLimiter {
	return g.rateLimiter
}

// getNextURL 獲取下一個服務 URL（輪詢負載均衡）
func (g *GatewayService) getNextURL() *url.URL {
	g.mu.Lock()
	defer g.mu.Unlock()

	url := g.orderServiceURLs[g.currentIndex]
	g.currentIndex = (g.currentIndex + 1) % len(g.orderServiceURLs)
	return url
}

// Proxy 代理請求到後端服務
func (g *GatewayService) Proxy(c *gin.Context) {
	target := g.getNextURL()
	
	proxy := httputil.NewSingleHostReverseProxy(target)
	proxy.ErrorHandler = func(w http.ResponseWriter, r *http.Request, err error) {
		// 如果一個服務失敗，嘗試下一個
		nextTarget := g.getNextURL()
		if nextTarget != target {
			proxy := httputil.NewSingleHostReverseProxy(nextTarget)
			proxy.ServeHTTP(w, r)
			return
		}
		http.Error(w, "服務不可用", http.StatusServiceUnavailable)
	}

	// 修改請求
	c.Request.URL.Host = target.Host
	c.Request.URL.Scheme = target.Scheme
	c.Request.Header.Set("X-Forwarded-Host", c.Request.Header.Get("Host"))
	c.Request.Host = target.Host

	proxy.ServeHTTP(c.Writer, c.Request)
}

func (g *GatewayService) Close() {
	// 清理資源
}

