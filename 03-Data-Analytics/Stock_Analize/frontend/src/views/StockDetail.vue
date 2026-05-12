<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div class="flex items-center">
          <router-link to="/" class="text-primary-600 hover:text-primary-900 mr-4">
            ← 返回
          </router-link>
          <h1 class="text-2xl font-bold text-gray-900">
            {{ stock.name || symbol }} ({{ symbol }})
          </h1>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div v-if="loading" class="text-center py-12 text-gray-500">
        載入中...
      </div>
      
      <div v-else-if="!stock" class="text-center py-12 text-gray-500">
        找不到股票資料
      </div>
      
      <div v-else>
        <!-- Price Info -->
        <div class="bg-white rounded-lg shadow p-6 mb-6">
          <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div>
              <div class="text-sm font-medium text-gray-500">最新價</div>
              <div class="mt-2 text-2xl font-bold text-gray-900">
                {{ formatNumber(price.close) }}
              </div>
            </div>
            <div>
              <div class="text-sm font-medium text-gray-500">開盤</div>
              <div class="mt-2 text-xl font-semibold text-gray-900">
                {{ formatNumber(price.open) }}
              </div>
            </div>
            <div>
              <div class="text-sm font-medium text-gray-500">最高</div>
              <div class="mt-2 text-xl font-semibold text-red-600">
                {{ formatNumber(price.high) }}
              </div>
            </div>
            <div>
              <div class="text-sm font-medium text-gray-500">最低</div>
              <div class="mt-2 text-xl font-semibold text-green-600">
                {{ formatNumber(price.low) }}
              </div>
            </div>
          </div>
          
          <div class="mt-6 pt-6 border-t border-gray-200">
            <div class="flex items-center justify-between">
              <div>
                <div class="text-sm font-medium text-gray-500">漲跌</div>
                <div class="mt-2 text-2xl font-bold" :class="getChangeColor(price.change)">
                  {{ formatChange(price.change) }}
                  ({{ formatPercent(price.change_percent) }})
                </div>
              </div>
              <div>
                <div class="text-sm font-medium text-gray-500">成交量</div>
                <div class="mt-2 text-xl font-semibold text-gray-900">
                  {{ formatNumber(price.volume) }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Chart Placeholder -->
        <div class="bg-white rounded-lg shadow p-6 mb-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-4">價格走勢圖</h2>
          <div class="h-64 flex items-center justify-center text-gray-400 border-2 border-dashed border-gray-300 rounded">
            圖表功能開發中...
          </div>
        </div>

        <!-- History Table -->
        <div class="bg-white rounded-lg shadow">
          <div class="px-6 py-4 border-b border-gray-200">
            <h2 class="text-lg font-semibold text-gray-900">歷史價格</h2>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">日期</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">開盤</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">最高</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">最低</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">收盤</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">成交量</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="item in history" :key="item.date" class="hover:bg-gray-50">
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ item.date }}</td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ formatNumber(item.open) }}</td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-red-600">{{ formatNumber(item.high) }}</td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-green-600">{{ formatNumber(item.low) }}</td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ formatNumber(item.close) }}</td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ formatNumber(item.volume) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { stockAPI } from '../services/api'

const route = useRoute()
const symbol = route.params.symbol

const loading = ref(true)
const stock = ref(null)
const price = ref({})
const history = ref([])

const loadData = async () => {
  try {
    loading.value = true
    
    const [stockRes, priceRes, historyRes] = await Promise.all([
      stockAPI.getStock(symbol),
      stockAPI.getLatestPrice(symbol),
      stockAPI.getPriceHistory(symbol, { limit: 30 })
    ])
    
    stock.value = stockRes.data
    price.value = priceRes.data || {}
    history.value = historyRes.data || []
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
})
</script>
