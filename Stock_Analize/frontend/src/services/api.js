import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 10000
})

// 請求攔截器
api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 回應攔截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// API 方法
export const stockAPI = {
  // 取得所有股票
  getStocks: (params) => api.get('/stocks', { params }),
  
  // 取得特定股票
  getStock: (symbol) => api.get(`/stocks/${symbol}`),
  
  // 新增股票
  createStock: (data) => api.post('/stocks', data),
  
  // 刪除股票
  deleteStock: (symbol) => api.delete(`/stocks/${symbol}`),
  
  // 取得最新價格
  getLatestPrice: (symbol) => api.get(`/stocks/${symbol}/price`),
  
  // 取得歷史價格
  getPriceHistory: (symbol, params) => api.get(`/stocks/${symbol}/history`, { params }),
  
  // 取得技術指標
  getIndicators: (symbol, params) => api.get(`/stocks/${symbol}/indicators`, { params }),
  
  // 取得特定指標
  getIndicator: (symbol, indicatorType, params) => 
    api.get(`/stocks/${symbol}/indicators/${indicatorType}`, { params })
}

export const dashboardAPI = {
  // 取得儀表板摘要
  getSummary: () => api.get('/dashboard/summary'),
  
  // 取得漲幅排行榜
  getTopGainers: (limit = 10) => api.get('/dashboard/top-gainers', { params: { limit } }),
  
  // 取得跌幅排行榜
  getTopLosers: (limit = 10) => api.get('/dashboard/top-losers', { params: { limit } })
}

export default api

// 注意：期貨相關 API 請使用 futuresApi.js
