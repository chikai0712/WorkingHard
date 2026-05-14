package order

import (
	"time"
)

// Order 注單模型
type Order struct {
	ID          int64     `json:"id" db:"id"`
	UserID      int64     `json:"user_id" db:"user_id"`
	OrderNo     string    `json:"order_no" db:"order_no"`         // 注單號（唯一）
	GameType    string    `json:"game_type" db:"game_type"`       // 遊戲類型
	BetAmount   float64   `json:"bet_amount" db:"bet_amount"`     // 投注金額
	WinAmount   float64   `json:"win_amount" db:"win_amount"`     // 贏取金額
	Status      string    `json:"status" db:"status"`             // pending, settled, cancelled
	BetTime     time.Time `json:"bet_time" db:"bet_time"`         // 投注時間
	SettleTime  *time.Time `json:"settle_time,omitempty" db:"settle_time"` // 結算時間
	CreatedAt   time.Time `json:"created_at" db:"created_at"`
	UpdatedAt   time.Time `json:"updated_at" db:"updated_at"`
}

// OrderRequest 創建注單請求
type OrderRequest struct {
	UserID    int64   `json:"user_id" binding:"required"`
	GameType  string  `json:"game_type" binding:"required"`
	BetAmount float64 `json:"bet_amount" binding:"required,gt=0"`
	OrderNo   string  `json:"order_no" binding:"required"`
}

// OrderResponse 注單響應
type OrderResponse struct {
	ID        int64     `json:"id"`
	OrderNo   string    `json:"order_no"`
	Status    string    `json:"status"`
	BetAmount float64   `json:"bet_amount"`
	CreatedAt time.Time `json:"created_at"`
}

// OrderQueryRequest 查詢注單請求
type OrderQueryRequest struct {
	UserID   *int64     `json:"user_id"`
	OrderNo  *string    `json:"order_no"`
	Status   *string    `json:"status"`
	StartTime *time.Time `json:"start_time"`
	EndTime   *time.Time `json:"end_time"`
	Page     int        `json:"page" binding:"min=1"`
	PageSize int        `json:"page_size" binding:"min=1,max=100"`
}

// OrderListResponse 注單列表響應
type OrderListResponse struct {
	Orders []OrderResponse `json:"orders"`
	Total  int64           `json:"total"`
	Page   int             `json:"page"`
	PageSize int           `json:"page_size"`
}

