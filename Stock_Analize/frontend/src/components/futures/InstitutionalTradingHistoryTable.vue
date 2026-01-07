<template>
  <div class="bg-white rounded-lg shadow">
    <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
      <h2 class="text-lg font-semibold text-gray-900">近7日上市三大法人買賣超</h2>
      <button class="text-sm text-primary-600 hover:text-primary-900">看更多</button>
    </div>
    
    <div v-if="loading" class="p-8 text-center text-gray-500">
      載入中...
    </div>
    
    <div v-else-if="!data || data.length === 0" class="p-8 text-center text-gray-500">
      目前沒有資料
    </div>
    
    <div v-else class="overflow-x-auto">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">日期</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">外資</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">投信</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">自營(總)</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">自營自買</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">自營避險</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">總計</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="item in data" :key="item.date" class="hover:bg-gray-50">
            <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-900">{{ formatDate(item.date) }}</td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-900 text-right">
              {{ formatNumber(item.foreign?.net) }}
            </td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-900 text-right">
              {{ formatNumber(item.trust?.net) }}
            </td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-900 text-right">
              {{ formatNumber(item.dealer?.net) }}
            </td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-900 text-right">
              {{ formatNumber(item.dealer?.self_net) }}
            </td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-900 text-right">
              {{ formatNumber(item.dealer?.hedge_net) }}
            </td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-right font-semibold" :class="getNetColor(item.total_net)">
              {{ formatNumber(item.total_net) }}
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
  return new Intl.NumberFormat('zh-TW', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(num)
}

const getNetColor = (net) => {
  if (net === null || net === undefined) return 'text-gray-900'
  return net >= 0 ? 'text-red-600' : 'text-green-600'
}
</script>

