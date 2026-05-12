package common

import (
	"context"
	"sync"
)

// GoroutinePool 控制並發數量的 Goroutine 池
type GoroutinePool struct {
	workers    int
	jobQueue   chan func()
	wg         sync.WaitGroup
	ctx        context.Context
	cancel     context.CancelFunc
}

// NewGoroutinePool 創建新的 Goroutine 池
func NewGoroutinePool(workers int, queueSize int) *GoroutinePool {
	ctx, cancel := context.WithCancel(context.Background())
	pool := &GoroutinePool{
		workers:  workers,
		jobQueue: make(chan func(), queueSize),
		ctx:      ctx,
		cancel:   cancel,
	}

	// 啟動 worker
	for i := 0; i < workers; i++ {
		pool.wg.Add(1)
		go pool.worker()
	}

	return pool
}

// worker 工作協程
func (p *GoroutinePool) worker() {
	defer p.wg.Done()
	for {
		select {
		case <-p.ctx.Done():
			return
		case job := <-p.jobQueue:
			if job != nil {
				job()
			}
		}
	}
}

// Submit 提交任務
func (p *GoroutinePool) Submit(job func()) bool {
	select {
	case <-p.ctx.Done():
		return false
	case p.jobQueue <- job:
		return true
	default:
		// 隊列滿了，可以選擇阻塞或返回錯誤
		return false
	}
}

// Shutdown 關閉池
func (p *GoroutinePool) Shutdown() {
	close(p.jobQueue)
	p.cancel()
	p.wg.Wait()
}

// QueueSize 返回當前隊列大小
func (p *GoroutinePool) QueueSize() int {
	return len(p.jobQueue)
}

