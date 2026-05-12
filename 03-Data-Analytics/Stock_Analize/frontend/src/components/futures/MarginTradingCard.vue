<template>
  <div class="bg-white rounded-lg shadow">
    <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
      <div>
        <h2 class="text-lg font-semibold text-gray-900">融資融券餘額</h2>
        <div v-if="data" class="text-sm text-gray-500 mt-1">
          {{ formatDate(data.date) }}
        </div>
      </div>
      <button class="text-sm text-primary-600 hover:text-primary-900">看更多</button>
    </div>
    
    <div v-if="loading" class="p-8 text-center text-gray-500">
      載入中...
    </div>
    
    <div v-else-if="!data" class="p-8 text-center text-gray-500">
      目前沒有資料
    </div>
    
    <div v-else class="p-6">
      <!-- 最新資料卡片 -->
      <!-- 最新資料表格 -->
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">項目</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">餘額</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">昨日差異</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <!-- 融資 -->
            <tr>
              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">融資</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                {{ formatNumber(data.margin?.balance) }} 億
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-right font-semibold" :class="getChangeColor(data.margin?.change)">
                {{ formatChange(data.margin?.change) }} 億
              </td>
            </tr>
            
            <!-- 融券 -->
            <tr>
              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">融券</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                {{ formatNumber(data.short_selling?.balance) }} 張
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-right font-semibold" :class="getChangeColor(data.short_selling?.change)">
                {{ formatChange(data.short_selling?.change) }} 張
              </td>
            </tr>
            
            <!-- 借券賣出 -->
            <tr>
              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">借券賣出</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                {{ formatNumber(data.securities_lending?.sell) || 0 }} 張
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-right font-semibold" :class="getChangeColor(data.securities_lending?.change)">
                {{ data.securities_lending?.change !== null && data.securities_lending?.change !== undefined ? formatChange(data.securities_lending.change) + ' 張' : '-' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
    </div>
  </div>
</template>

<script setup>
defineProps({
  data: Object,
  loading: Boolean
})

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}/${month}/${day}`
}

const formatNumber = (num) => {
  if (num === null || num === undefined) return '-'
  return new Intl.NumberFormat('zh-TW', { minimumFractionDigits: 1, maximumFractionDigits: 1 }).format(num)
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

const getChangeColor = (value) => {
  if (value === null || value === undefined) return 'text-gray-900'
  // 注意：融資融券的增減，正數用紅色，負數用綠色（與股票相反）
  return value >= 0 ? 'text-red-600' : 'text-green-600'
}
</script>
