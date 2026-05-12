<template>
  <div class="bg-white rounded-lg shadow">
    <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
      <h2 class="text-lg font-semibold text-gray-900">近十日台指選擇權交易及未平倉口數</h2>
      <button class="text-sm text-primary-600 hover:text-primary-900">看更多</button>
    </div>
    
    <div v-if="loading" class="p-8 text-center text-gray-500">
      載入中...
    </div>
    
    <div v-else-if="!data || data.length === 0" class="p-8 text-center text-gray-500">
      目前沒有資料
    </div>
    
    <div v-else class="overflow-x-auto">
      <table class="min-w-full divide-y divide-gray-200 text-sm">
        <thead class="bg-gray-50">
          <tr>
            <th rowspan="2" class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase border-r">日期</th>
            <th colspan="3" class="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase border-r">台股大盤</th>
            <th colspan="3" class="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase border-r">交易口數淨額</th>
            <th rowspan="2" class="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase border-r">P/C比</th>
            <th colspan="3" class="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase border-r">未平倉口數</th>
            <th rowspan="2" class="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase">P/C比</th>
          </tr>
          <tr>
            <!-- 台股大盤子標題 -->
            <th class="px-2 py-2 text-center text-xs font-medium text-gray-500">指數</th>
            <th class="px-2 py-2 text-center text-xs font-medium text-gray-500">漲跌</th>
            <th class="px-2 py-2 text-center text-xs font-medium text-gray-500 border-r">漲跌幅</th>
            <!-- 交易口數淨額子標題 -->
            <th class="px-2 py-2 text-center text-xs font-medium text-gray-500">外資</th>
            <th class="px-2 py-2 text-center text-xs font-medium text-gray-500">投信</th>
            <th class="px-2 py-2 text-center text-xs font-medium text-gray-500 border-r">自營</th>
            <!-- 未平倉口數子標題 -->
            <th class="px-2 py-2 text-center text-xs font-medium text-gray-500">外資</th>
            <th class="px-2 py-2 text-center text-xs font-medium text-gray-500">投信</th>
            <th class="px-2 py-2 text-center text-xs font-medium text-gray-500 border-r">自營</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="item in data" :key="item.date" class="hover:bg-gray-50">
            <!-- 日期 -->
            <td class="px-3 py-3 whitespace-nowrap text-gray-900 border-r">{{ formatDate(item.date) }}</td>
            
            <!-- 台股大盤 -->
            <td class="px-2 py-3 whitespace-nowrap text-right text-gray-900">
              {{ formatNumber(item.index_price) }}
            </td>
            <td class="px-2 py-3 whitespace-nowrap text-right" :class="getChangeColor(item.change)">
              {{ formatChange(item.change) }}
            </td>
            <td class="px-2 py-3 whitespace-nowrap text-right border-r" :class="getChangePercentColor(item.change_percent)">
              {{ formatChangePercent(item.change_percent) }}
            </td>
            
            <!-- 交易口數淨額 -->
            <td class="px-2 py-3 whitespace-nowrap text-right" :class="getNetVolumeColor(item.foreign?.net_volume)">
              {{ formatNumber(item.foreign?.net_volume) }}
            </td>
            <td class="px-2 py-3 whitespace-nowrap text-right" :class="getNetVolumeColor(item.trust?.net_volume)">
              {{ formatNumber(item.trust?.net_volume) }}
            </td>
            <td class="px-2 py-3 whitespace-nowrap text-right border-r" :class="getNetVolumeColor(item.dealer?.net_volume)">
              {{ formatNumber(item.dealer?.net_volume) }}
            </td>
            
            <!-- 交易口數P/C比 -->
            <td class="px-3 py-3 whitespace-nowrap text-center text-gray-900 border-r">
              {{ formatPCRatio(item.pc_ratio_volume) }}
            </td>
            
            <!-- 未平倉口數（外資、投信、自營，每欄顯示兩行：未平倉量 + 昨日差異） -->
            <td class="px-2 py-3 whitespace-nowrap text-right">
              <div :class="getOIColor(item.foreign?.oi)">
                {{ formatNumber(item.foreign?.oi) }}
              </div>
              <div class="text-xs mt-1" :class="getChangeColor(item.foreign?.oi_change)">
                {{ formatChangeWithArrow(item.foreign?.oi_change) }}
              </div>
            </td>
            <td class="px-2 py-3 whitespace-nowrap text-right">
              <div :class="getOIColor(item.trust?.oi)">
                {{ formatNumber(item.trust?.oi) }}
              </div>
              <div class="text-xs mt-1" :class="getChangeColor(item.trust?.oi_change)">
                {{ formatChangeWithArrow(item.trust?.oi_change) }}
              </div>
            </td>
            <td class="px-2 py-3 whitespace-nowrap text-right border-r">
              <div :class="getOIColor(item.dealer?.oi)">
                {{ formatNumber(item.dealer?.oi) }}
              </div>
              <div class="text-xs mt-1" :class="getChangeColor(item.dealer?.oi_change)">
                {{ formatChangeWithArrow(item.dealer?.oi_change) }}
              </div>
            </td>
            
            <!-- 未平倉P/C比 -->
            <td class="px-3 py-3 whitespace-nowrap text-center font-semibold text-gray-900">
              {{ formatPCRatio(item.pc_ratio_oi) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
defineProps({
  data: Array,
  loading: Boolean
})

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${month}/${day}`
}

const formatNumber = (num) => {
  if (num === null || num === undefined) return '-'
  return new Intl.NumberFormat('zh-TW').format(num)
}

const formatChange = (change) => {
  if (change === null || change === undefined || change === 0) return '-'
  const sign = change >= 0 ? '+' : ''
  return `${sign}${change.toLocaleString('zh-TW')}`
}

const formatChangePercent = (percent) => {
  if (percent === null || percent === undefined || percent === 0) return '-'
  const sign = percent >= 0 ? '▲' : '▼'
  const absPercent = Math.abs(percent)
  return `${sign}${absPercent.toFixed(2)}`
}

const formatChangeWithArrow = (change) => {
  if (change === null || change === undefined || change === 0) return '-'
  const sign = change >= 0 ? '▲' : '▼'
  const absChange = Math.abs(change)
  return `${sign}${absChange.toLocaleString('zh-TW')}`
}

const formatPCRatio = (ratio) => {
  if (ratio === null || ratio === undefined) return '-'
  return `${ratio.toFixed(1)}%`
}

const getOIColor = (oi) => {
  if (oi === null || oi === undefined) return 'text-gray-900'
  return oi >= 0 ? 'text-red-600' : 'text-green-600'
}

const getChangeColor = (change) => {
  if (change === null || change === undefined || change === 0) return 'text-gray-500'
  return change >= 0 ? 'text-red-600' : 'text-green-600'
}

const getChangePercentColor = (percent) => {
  if (percent === null || percent === undefined || percent === 0) return 'text-gray-500'
  return percent >= 0 ? 'text-red-600' : 'text-green-600'
}

const getNetVolumeColor = (volume) => {
  if (volume === null || volume === undefined || volume === 0) return 'text-gray-900'
  return volume >= 0 ? 'text-red-600' : 'text-green-600'
}
</script>

