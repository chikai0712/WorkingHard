import api from './api'

// 期貨相關 API
export const futuresAPI = {
  // 取得期貨每日交易資料
  getDaily: (params) => api.get('/futures/daily', { params }),
  
  // 取得三大法人買賣超
  getInstitutional: (params) => api.get('/futures/institutional', { params }),
  
  // 取得期貨未平倉量
  getOpenInterest: (params) => api.get('/futures/open-interest', { params }),
  
  // 取得融資融券餘額
  getMarginTrading: (params) => api.get('/futures/trading', { params }),
}

// 選擇權相關 API
export const optionsAPI = {
  // 取得選擇權未平倉量
  getOpenInterest: (params) => api.get('/futures/options/open-interest', { params }),
  
  // 取得選擇權履約價分布
  getStrikeData: (params) => api.get('/futures/options/strike-data', { params }),
  
  // 取得選擇權每日交易資料
  getDaily: (params) => api.get('/futures/options/daily', { params }),
}

