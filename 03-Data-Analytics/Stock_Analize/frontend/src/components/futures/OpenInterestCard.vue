<template>
  <div class="bg-white rounded-lg shadow">
    <div class="px-6 py-4 border-b border-gray-200">
      <h2 class="text-lg font-semibold text-gray-900">期貨未平倉量</h2>
      <div v-if="data" class="text-sm text-gray-500 mt-1">
        日期：{{ data.date }}
      </div>
    </div>
    
    <div v-if="loading" class="p-8 text-center text-gray-500">
      載入中...
    </div>
    
    <div v-else-if="!data" class="p-8 text-center text-gray-500">
      目前沒有資料
    </div>
    
    <div v-else class="p-6">
      <!-- 三大法人未平倉 -->
      <div class="mb-6">
        <h3 class="text-sm font-medium text-gray-700 mb-4">三大法人</h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <!-- 外資 -->
          <div class="bg-gray-50 rounded-lg p-4">
            <div class="text-sm font-medium text-gray-500 mb-2">外資</div>
            <div class="text-xl font-bold mb-1" :class="getOIColor(data.foreign?.oi)">
              {{ formatNumber(data.foreign?.oi) }}
            </div>
            <div class="text-sm" :class="getChangeColor(data.foreign?.oi_change)">
              {{ formatChange(data.foreign?.oi_change) }}
            </div>
          </div>
          
          <!-- 投信 -->
          <div class="bg-gray-50 rounded-lg p-4">
            <div class="text-sm font-medium text-gray-500 mb-2">投信</div>
            <div class="text-xl font-bold mb-1" :class="getOIColor(data.trust?.oi)">
              {{ formatNumber(data.trust?.oi) }}
            </div>
            <div class="text-sm" :class="getChangeColor(data.trust?.oi_change)">
              {{ formatChange(data.trust?.oi_change) }}
            </div>
          </div>
          
          <!-- 自營 -->
          <div class="bg-gray-50 rounded-lg p-4">
            <div class="text-sm font-medium text-gray-500 mb-2">自營</div>
            <div class="text-xl font-bold mb-1" :class="getOIColor(data.dealer?.oi)">
              {{ formatNumber(data.dealer?.oi) }}
            </div>
            <div class="text-sm" :class="getChangeColor(data.dealer?.oi_change)">
              {{ formatChange(data.dealer?.oi_change) }}
            </div>
          </div>
        </div>
      </div>
      
      <!-- 十大交易人與散戶 -->
      <div class="border-t border-gray-200 pt-6">
        <h3 class="text-sm font-medium text-gray-700 mb-4">十大交易人 & 散戶</h3>
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <!-- 前五大 -->
          <div class="bg-blue-50 rounded-lg p-4">
            <div class="text-sm font-medium text-gray-600 mb-2">前五大</div>
            <div class="text-lg font-bold mb-1" :class="getOIColor(data.top5?.oi)">
              {{ formatNumber(data.top5?.oi) }}
            </div>
            <div class="text-xs" :class="getChangeColor(data.top5?.oi_change)">
              {{ formatChange(data.top5?.oi_change) }}
            </div>
          </div>
          
          <!-- 前十大 -->
          <div class="bg-blue-50 rounded-lg p-4">
            <div class="text-sm font-medium text-gray-600 mb-2">前十大</div>
            <div class="text-lg font-bold mb-1" :class="getOIColor(data.top10?.oi)">
              {{ formatNumber(data.top10?.oi) }}
            </div>
            <div class="text-xs text-gray-500">-</div>
          </div>
          
          <!-- 前十大特定人 -->
          <div class="bg-purple-50 rounded-lg p-4">
            <div class="text-sm font-medium text-gray-600 mb-2">前十大特定人</div>
            <div class="text-lg font-bold mb-1" :class="getOIColor(data.top10_special?.oi)">
              {{ formatNumber(data.top10_special?.oi) }}
            </div>
            <div class="text-xs text-gray-500">-</div>
          </div>
          
          <!-- 散戶 -->
          <div class="bg-green-50 rounded-lg p-4">
            <div class="text-sm font-medium text-gray-600 mb-2">散戶</div>
            <div class="text-lg font-bold mb-1" :class="getOIColor(data.retail?.oi)">
              {{ formatNumber(data.retail?.oi) }}
            </div>
            <div class="text-xs" :class="getChangeColor(data.retail?.oi_change)">
              {{ formatChange(data.retail?.oi_change) }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  data: Object,
  loading: Boolean
})

const formatNumber = (num) => {
  if (num === null || num === undefined) return '-'
  return new Intl.NumberFormat('zh-TW').format(num)
}

const formatChange = (change) => {
  if (change === null || change === undefined) return '-'
  const sign = change >= 0 ? '+' : ''
  return `${sign}${change.toLocaleString('zh-TW')}`
}

const getOIColor = (oi) => {
  if (oi === null || oi === undefined) return 'text-gray-900'
  // 負數表示做空，正數表示做多
  return oi >= 0 ? 'text-red-600' : 'text-green-600'
}

const getChangeColor = (change) => {
  if (change === null || change === undefined) return 'text-gray-500'
  return change >= 0 ? 'text-red-600' : 'text-green-600'
}
</script>

