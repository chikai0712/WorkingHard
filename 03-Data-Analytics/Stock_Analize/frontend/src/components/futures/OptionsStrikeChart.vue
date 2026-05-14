<template>
  <div class="bg-white rounded-lg shadow">
    <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
      <h2 class="text-lg font-semibold text-gray-900">{{ title }}</h2>
      <div v-if="data" class="text-sm text-gray-500">
        {{ data.contract_code }} | {{ data.date }}
      </div>
    </div>
    
    <div v-if="loading" class="p-8 text-center text-gray-500">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto mb-2"></div>
      載入中...
    </div>
    
    <div v-else-if="!data || !data.strike_data || data.strike_data.length === 0" class="p-8 text-center text-gray-500">
      目前沒有資料
    </div>
    
    <div v-else class="p-6">
      <!-- 指數資訊 -->
      <div v-if="data.index_price" class="mb-4 pb-4 border-b border-gray-200">
        <div class="flex items-center justify-between">
          <div>
            <span class="text-sm text-gray-500">指數：</span>
            <span class="text-lg font-semibold text-gray-900">{{ formatNumber(data.index_price) }}</span>
          </div>
          <div v-if="data.change_percent" class="text-sm" :class="getChangeColor(data.change_percent)">
            {{ formatPercent(data.change_percent) }}
          </div>
        </div>
      </div>
      
      <!-- 選擇權分布圖 -->
      <div class="relative" style="height: 500px; overflow-y: auto;">
        <div class="space-y-2">
          <div
            v-for="strike in data.strike_data"
            :key="strike.strike_price"
            class="flex items-center"
            :class="{ 'bg-blue-50': isAtTheMoney(strike.strike_price) }"
          >
            <!-- 買權OI (左側，紅色條) -->
            <div class="flex-1 flex items-center justify-end pr-2">
              <div class="flex items-center" :style="{ width: `${getCallOIWidth(strike.call.oi)}%`, justifyContent: 'flex-end' }">
                <div class="bg-red-400 h-6 rounded-l flex items-center justify-end pr-2 min-w-[60px]">
                  <span class="text-xs font-medium text-white">{{ formatNumber(strike.call.oi) }}</span>
                  <span v-if="strike.call.oi_change" class="text-xs text-red-100 ml-1">
                    ({{ formatChange(strike.call.oi_change) }})
                  </span>
                </div>
              </div>
            </div>
            
            <!-- 履約價 (中間) -->
            <div class="w-20 text-center text-sm font-semibold text-gray-900 px-2">
              {{ strike.strike_price }}
            </div>
            
            <!-- 賣權OI (右側，綠色條) -->
            <div class="flex-1 flex items-center justify-start pl-2">
              <div class="flex items-center" :style="{ width: `${getPutOIWidth(strike.put.oi)}%` }">
                <div class="bg-green-400 h-6 rounded-r flex items-center justify-start pl-2 min-w-[60px]">
                  <span class="text-xs font-medium text-white">{{ formatNumber(strike.put.oi) }}</span>
                  <span v-if="strike.put.oi_change" class="text-xs text-green-100 ml-1">
                    ({{ formatChange(strike.put.oi_change) }})
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 圖例 -->
      <div class="mt-4 pt-4 border-t border-gray-200 flex items-center justify-center space-x-6 text-sm">
        <div class="flex items-center">
          <div class="w-8 h-4 bg-red-400 rounded mr-2"></div>
          <span class="text-gray-600">買權OI (單位:口)</span>
        </div>
        <div class="flex items-center">
          <div class="w-8 h-4 bg-green-400 rounded mr-2"></div>
          <span class="text-gray-600">賣權OI (單位:口)</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: String,
  period: String,
  data: Object,
  loading: Boolean
})

// 計算最大OI值用於比例計算
const maxOI = computed(() => {
  if (!props.data || !props.data.strike_data) return 10000
  let max = 0
  props.data.strike_data.forEach(strike => {
    if (strike.call?.oi > max) max = strike.call.oi
    if (strike.put?.oi > max) max = strike.put.oi
  })
  return max || 10000
})

// 計算買權OI寬度百分比
const getCallOIWidth = (oi) => {
  if (!oi || oi === 0) return 0
  return Math.min((oi / maxOI.value) * 100, 50) // 最多50%寬度
}

// 計算賣權OI寬度百分比
const getPutOIWidth = (oi) => {
  if (!oi || oi === 0) return 0
  return Math.min((oi / maxOI.value) * 100, 50) // 最多50%寬度
}

// 判斷是否為價平
const isAtTheMoney = (strikePrice) => {
  if (!props.data || !props.data.index_price) return false
  const index = props.data.index_price
  const diff = Math.abs(strikePrice - index)
  return diff < 100 // 履約價與指數差距小於100視為價平
}

const formatNumber = (num) => {
  if (num === null || num === undefined) return '0'
  return new Intl.NumberFormat('zh-TW').format(num)
}

const formatChange = (change) => {
  if (change === null || change === undefined) return ''
  const sign = change >= 0 ? '+' : ''
  return `${sign}${change.toLocaleString('zh-TW')}`
}

const formatPercent = (percent) => {
  if (percent === null || percent === undefined) return ''
  const sign = percent >= 0 ? '+' : ''
  return `${sign}${percent.toFixed(2)}%`
}

const getChangeColor = (value) => {
  if (value === null || value === undefined) return 'text-gray-900'
  return value >= 0 ? 'text-red-600' : 'text-green-600'
}
</script>

