package common

import (
	"sync"
	"time"
)

// RateLimiter Token Bucket 限流器
type RateLimiter struct {
	tokens    int64
	maxTokens int64
	rate      int64 // tokens per second
	lastTime  time.Time
	mu        sync.Mutex
}

// NewRateLimiter 創建新的限流器
func NewRateLimiter(maxTokens int64, rate int64) *RateLimiter {
	return &RateLimiter{
		tokens:    maxTokens,
		maxTokens: maxTokens,
		rate:      rate,
		lastTime:  time.Now(),
	}
}

// Allow 檢查是否允許請求
func (rl *RateLimiter) Allow() bool {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	now := time.Now()
	elapsed := now.Sub(rl.lastTime).Seconds()
	
	// 補充 token
	newTokens := int64(elapsed * float64(rl.rate))
	if newTokens > 0 {
		rl.tokens = min(rl.tokens+newTokens, rl.maxTokens)
		rl.lastTime = now
	}

	if rl.tokens > 0 {
		rl.tokens--
		return true
	}

	return false
}

// AllowN 檢查是否允許 N 個請求
func (rl *RateLimiter) AllowN(n int64) bool {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	now := time.Now()
	elapsed := now.Sub(rl.lastTime).Seconds()
	
	// 補充 token
	newTokens := int64(elapsed * float64(rl.rate))
	if newTokens > 0 {
		rl.tokens = min(rl.tokens+newTokens, rl.maxTokens)
		rl.lastTime = now
	}

	if rl.tokens >= n {
		rl.tokens -= n
		return true
	}

	return false
}

func min(a, b int64) int64 {
	if a < b {
		return a
	}
	return b
}

