<template>
  <div class="bg-white rounded-lg shadow">
    <div class="px-6 py-4 border-b border-gray-200">
      <h2 class="text-lg font-semibold text-gray-900">期貨交易及未平倉口數（近30日）</h2>
    </div>
    
    <div v-if="loading" class="p-8 text-center text-gray-500">
      載入中...
    </div>
    
    <div v-else-if="!data || data.length === 0" class="p-8 text-center text-gray-500">
      目前沒有歷史資料
    </div>
    
    <div v-else class="overflow-x-auto">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">日期</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">指數</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">漲跌</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">漲跌幅</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">成交量(口)</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">未平倉(口)</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr
            v-for="item in data"
            :key="item.date"
            class="hover:bg-gray-50"
          >
            <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-900">{{ item.date }}</td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-900 text-right">
              {{ formatNumber(item.close) }}
            </td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-right font-semibold" :class="getChangeColor(item.change)">
              {{ formatChange(item.change) }}
            </td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-right" :class="getChangeColor(item.change_percent)">
              {{ formatPercent(item.change_percent) }}
            </td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-900 text-right">
              {{ formatNumber(item.volume) }}
            </td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-900 text-right">
              {{ formatNumber(item.open_interest) }}
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

const getChangeColor = (value) => {
  if (value === null || value === undefined) return 'text-gray-900'
  return value >= 0 ? 'text-red-600' : 'text-green-600'
}
</script>

