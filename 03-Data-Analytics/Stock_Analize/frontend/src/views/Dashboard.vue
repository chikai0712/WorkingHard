<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div class="flex items-center justify-between">
          <h1 class="text-2xl font-bold text-gray-900">股票資訊儀表板</h1>
          <router-link
            to="/futures"
            class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            台指期貨儀表板
          </router-link>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Summary Cards -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg shadow p-6">
          <div class="text-sm font-medium text-gray-500">總股票數</div>
          <div class="mt-2 text-3xl font-bold text-gray-900">
            {{ summary.total_stocks || 0 }}
          </div>
        </div>
        
        <div class="bg-white rounded-lg shadow p-6">
          <div class="text-sm font-medium text-gray-500">總市值</div>
          <div class="mt-2 text-3xl font-bold text-gray-900">
            {{ formatNumber(summary.total_value) }}
          </div>
        </div>
        
        <div class="bg-white rounded-lg shadow p-6">
          <div class="text-sm font-medium text-gray-500">總漲跌</div>
          <div class="mt-2 text-3xl font-bold" :class="getChangeColor(summary.total_change)">
            {{ formatChange(summary.total_change) }}
            ({{ formatPercent(summary.total_change_percent) }})
          </div>
        </div>
        
        <div class="bg-white rounded-lg shadow p-6">
          <div class="text-sm font-medium text-gray-500">上漲家數</div>
          <div class="mt-2 text-3xl font-bold text-green-600">
            {{ summary.gaining_stocks || 0 }}
          </div>
        </div>
      </div>

      <!-- Stock List -->
      <div class="bg-white rounded-lg shadow">
        <div class="px-6 py-4 border-b border-gray-200">
          <h2 class="text-lg font-semibold text-gray-900">監控股票列表</h2>
        </div>
        
        <div v-if="loading" class="p-8 text-center text-gray-500">
          載入中...
        </div>
        
        <div v-else-if="stocks.length === 0" class="p-8 text-center text-gray-500">
          目前沒有監控的股票，請先新增股票
        </div>
        
        <div v-else class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  代號
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  名稱
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  最新價
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  漲跌
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  成交量
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  操作
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="stock in stocks" :key="stock.id" class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {{ stock.symbol }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ stock.name }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {{ stock.current_price ? formatNumber(stock.current_price) : '-' }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm" :class="getChangeColor(stock.change)">
                  {{ formatChange(stock.change) }}
                  <span v-if="stock.change_percent !== null && stock.change_percent !== undefined">
                    ({{ formatPercent(stock.change_percent) }})
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ stock.volume ? formatNumber(stock.volume) : '-' }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">
                  <router-link
                    :to="`/stock/${stock.symbol}`"
                    class="text-primary-600 hover:text-primary-900"
                  >
                    查看詳情
                  </router-link>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { stockAPI, dashboardAPI } from '../services/api'

const loading = ref(true)
const stocks = ref([])
const summary = ref({})

const loadData = async () => {
  try {
    loading.value = true
    
    // 並行載入資料
    const [stocksRes, summaryRes] = await Promise.all([
      stockAPI.getStocks(),
      dashboardAPI.getSummary()
    ])
    
    stocks.value = stocksRes.data || []
    summary.value = summaryRes.data || {}
  } catch (error) {
    console.error('載入資料失敗:', error)
  } finally {
    loading.value = false
  }
}

const formatNumber = (num) => {
  if (num === null || num === undefined) return '-'
  return new Intl.NumberFormat('zh-TW').format(num)
}

const formatChange = (change) => {
  if (change === null || change === undefined) return '-'
  const sign = change >= 0 ? '+' : ''
  return `${sign}${change.toFixed(2)}`
}

const formatPercent = (percent) => {
  if (percent === null || percent === undefined) return '-'
  const sign = percent >= 0 ? '+' : ''
  return `${sign}${percent.toFixed(2)}%`
}

const getChangeColor = (change) => {
  if (change === null || change === undefined) return 'text-gray-900'
  return change >= 0 ? 'text-red-600' : 'text-green-600'
}

onMounted(() => {
  loadData()
  
  // 定時更新（每30秒）
  const interval = parseInt(import.meta.env.VITE_UPDATE_INTERVAL_SECONDS || 30) * 1000
  setInterval(loadData, interval)
})
</script>
