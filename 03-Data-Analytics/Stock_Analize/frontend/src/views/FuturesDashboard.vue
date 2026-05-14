<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white shadow-sm sticky top-0 z-10">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-4">
            <router-link to="/" class="text-primary-600 hover:text-primary-900">
              ← 返回股票儀表板
            </router-link>
            <h1 class="text-2xl font-bold text-gray-900">台指期貨儀表板</h1>
          </div>
          <div class="text-sm text-gray-500">
            最後更新：{{ lastUpdateTime || '--' }}
          </div>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Loading State -->
      <div v-if="loading" class="text-center py-12 text-gray-500">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
        載入中...
      </div>

      <!-- Content -->
      <div v-else class="space-y-6">
        <!-- 三大法人買賣超 -->
        <InstitutionalTradingCard :data="institutionalData" :loading="loadingInstitutional" />

        <!-- 融資融券餘額 -->
        <MarginTradingCard :data="marginData" :loading="loadingMargin" />

        <!-- 三大法人買賣超（卡片） -->
        <InstitutionalTradingCard :data="institutionalData" :loading="loadingInstitutional" />

        <!-- 三大法人買賣超（7天歷史表格） -->
        <InstitutionalTradingHistoryTable :data="institutionalHistoryData" :loading="loadingInstitutional" />

        <!-- 期貨未平倉量（卡片） -->
        <OpenInterestCard :data="openInterestData" :loading="loadingOpenInterest" />

        <!-- 期貨未平倉量（7天歷史表格） -->
        <FuturesOpenInterestHistoryTable :data="openInterestHistoryData" :loading="loadingOpenInterest" />

        <!-- 十大交易人（7天歷史表格） -->
        <TopTradersHistoryTable :data="topTradersHistoryData" :loading="loadingOpenInterest" />

        <!-- 選擇權未平倉量（7天歷史表格） -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- 周選擇權未平倉量 -->
          <OptionsOpenInterestHistoryTable 
            :data="weeklyOptionsOpenInterestData" 
            :loading="loadingWeeklyOptionsOI" 
          />
          
          <!-- 月選擇權未平倉量 -->
          <OptionsOpenInterestHistoryTable 
            :data="monthlyOptionsOpenInterestData" 
            :loading="loadingMonthlyOptionsOI" 
          />
        </div>

        <!-- 選擇權分布圖 -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- 周選擇權 -->
          <OptionsStrikeChart
            title="台指周選擇權每日交易行情"
            period="weekly"
            :data="weeklyOptionsData"
            :loading="loadingWeeklyOptions"
          />
          
          <!-- 月選擇權 -->
          <OptionsStrikeChart
            title="台指月選擇權每日交易行情"
            period="monthly"
            :data="monthlyOptionsData"
            :loading="loadingMonthlyOptions"
          />
        </div>

        <!-- 歷史資料表格 -->
        <FuturesHistoryTable :data="historyData" :loading="loadingHistory" />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { futuresAPI, optionsAPI } from '../services/futuresApi'
import InstitutionalTradingCard from '../components/futures/InstitutionalTradingCard.vue'
import MarginTradingCard from '../components/futures/MarginTradingCard.vue'
import OpenInterestCard from '../components/futures/OpenInterestCard.vue'
import OptionsStrikeChart from '../components/futures/OptionsStrikeChart.vue'
import FuturesHistoryTable from '../components/futures/FuturesHistoryTable.vue'
import InstitutionalTradingHistoryTable from '../components/futures/InstitutionalTradingHistoryTable.vue'
import FuturesOpenInterestHistoryTable from '../components/futures/FuturesOpenInterestHistoryTable.vue'
import TopTradersHistoryTable from '../components/futures/TopTradersHistoryTable.vue'
import OptionsOpenInterestHistoryTable from '../components/futures/OptionsOpenInterestHistoryTable.vue'

const loading = ref(true)
const loadingInstitutional = ref(false)
const loadingMargin = ref(false)
const loadingOpenInterest = ref(false)
const loadingWeeklyOptions = ref(false)
const loadingMonthlyOptions = ref(false)
const loadingWeeklyOptionsOI = ref(false)
const loadingMonthlyOptionsOI = ref(false)
const loadingHistory = ref(false)

const lastUpdateTime = ref('')
const institutionalData = ref(null)
const institutionalHistoryData = ref([])
const marginData = ref(null)
const marginHistoryData = ref([])
const openInterestData = ref(null)
const openInterestHistoryData = ref([])
const topTradersHistoryData = ref([])
const weeklyOptionsOpenInterestData = ref([])
const monthlyOptionsOpenInterestData = ref([])
const weeklyOptionsData = ref(null)
const monthlyOptionsData = ref(null)
const historyData = ref([])

const loadAllData = async () => {
  try {
    loading.value = true
    
    // 並行載入所有資料
    await Promise.all([
      loadInstitutionalData(),
      loadMarginData(),
      loadOpenInterestData(),
      loadWeeklyOptionsData(),
      loadMonthlyOptionsData(),
      loadWeeklyOptionsOpenInterestData(),
      loadMonthlyOptionsOpenInterestData(),
      loadHistoryData()
    ])
    
    lastUpdateTime.value = new Date().toLocaleString('zh-TW')
  } catch (error) {
    console.error('載入資料失敗:', error)
  } finally {
    loading.value = false
  }
}

const loadInstitutionalData = async () => {
  try {
    loadingInstitutional.value = true
    const response = await futuresAPI.getInstitutional({
      market_type: 'weighted',
      limit: 7  // 顯示7天資料
    })
    if (response.status === 'success' && response.data.length > 0) {
      institutionalData.value = response.data[0]  // 最新一筆
      institutionalHistoryData.value = response.data  // 保留7天歷史資料
    }
  } catch (error) {
    console.error('載入三大法人資料失敗:', error)
  } finally {
    loadingInstitutional.value = false
  }
}

const loadMarginData = async () => {
  try {
    loadingMargin.value = true
    const response = await futuresAPI.getMarginTrading({
      market_type: 'weighted',
      limit: 7  // 顯示7天資料
    })
    if (response.status === 'success' && response.data.length > 0) {
      // 取最新一筆作為主要顯示
      marginData.value = response.data[0]
      // 保留所有7天資料供表格顯示
      marginHistoryData.value = response.data
    }
  } catch (error) {
    console.error('載入融資融券資料失敗:', error)
  } finally {
    loadingMargin.value = false
  }
}

const loadOpenInterestData = async () => {
  try {
    loadingOpenInterest.value = true
    const response = await futuresAPI.getOpenInterest({
      symbol: 'TX',
      limit: 7  // 顯示7天資料
    })
    if (response.status === 'success' && response.data.length > 0) {
      openInterestData.value = response.data[0]  // 最新一筆
      openInterestHistoryData.value = response.data  // 保留7天歷史資料
      
      // 提取十大交易人資料
      topTradersHistoryData.value = response.data.map(item => ({
        date: item.date,
        top5: item.top5,
        top10: item.top10,
        top5_special: item.top5_special,
        top10_special: item.top10_special
      }))
    }
  } catch (error) {
    console.error('載入未平倉量資料失敗:', error)
  } finally {
    loadingOpenInterest.value = false
  }
}

const loadWeeklyOptionsData = async () => {
  try {
    loadingWeeklyOptions.value = true
    const response = await optionsAPI.getStrikeData({
      period: 'weekly'
    })
    if (response.status === 'success') {
      weeklyOptionsData.value = response
    }
  } catch (error) {
    console.error('載入周選擇權資料失敗:', error)
  } finally {
    loadingWeeklyOptions.value = false
  }
}

const loadMonthlyOptionsData = async () => {
  try {
    loadingMonthlyOptions.value = true
    const response = await optionsAPI.getStrikeData({
      period: 'monthly'
    })
    if (response.status === 'success') {
      monthlyOptionsData.value = response
    }
  } catch (error) {
    console.error('載入月選擇權資料失敗:', error)
  } finally {
    loadingMonthlyOptions.value = false
  }
}

const loadWeeklyOptionsOpenInterestData = async () => {
  try {
    loadingWeeklyOptionsOI.value = true
    const response = await optionsAPI.getOpenInterest({
      period: 'weekly',
      limit: 10  // 顯示10天資料
    })
    if (response.status === 'success') {
      weeklyOptionsOpenInterestData.value = response.data
    }
  } catch (error) {
    console.error('載入周選擇權未平倉量資料失敗:', error)
  } finally {
    loadingWeeklyOptionsOI.value = false
  }
}

const loadMonthlyOptionsOpenInterestData = async () => {
  try {
    loadingMonthlyOptionsOI.value = true
    const response = await optionsAPI.getOpenInterest({
      period: 'monthly',
      limit: 10  // 顯示10天資料
    })
    if (response.status === 'success') {
      monthlyOptionsOpenInterestData.value = response.data
    }
  } catch (error) {
    console.error('載入月選擇權未平倉量資料失敗:', error)
  } finally {
    loadingMonthlyOptionsOI.value = false
  }
}

const loadHistoryData = async () => {
  try {
    loadingHistory.value = true
    const response = await futuresAPI.getDaily({
      symbol: 'TX',
      limit: 30
    })
    if (response.status === 'success') {
      historyData.value = response.data
    }
  } catch (error) {
    console.error('載入歷史資料失敗:', error)
  } finally {
    loadingHistory.value = false
  }
}

onMounted(() => {
  loadAllData()
  
  // 定時更新（每30秒）
  const interval = parseInt(import.meta.env.VITE_UPDATE_INTERVAL_SECONDS || 30) * 1000
  setInterval(loadAllData, interval)
})
</script>

