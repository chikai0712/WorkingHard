<template>
  <div class="bg-white rounded-lg shadow">
    <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
      <h2 class="text-lg font-semibold text-gray-900">近7日十大交易人進出</h2>
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
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">前五大</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">前十大</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">前五特</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">前十特</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="item in data" :key="item.date" class="hover:bg-gray-50">
            <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-900">{{ formatDate(item.date) }}</td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-right" :class="getValueColor(item.top5?.oi)">
              {{ formatNumber(item.top5?.oi) }}
            </td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-right" :class="getValueColor(item.top10?.oi)">
              {{ formatNumber(item.top10?.oi) }}
            </td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-right" :class="getValueColor(item.top5_special?.oi)">
              {{ formatNumber(item.top5_special?.oi) }}
            </td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-right" :class="getValueColor(item.top10_special?.oi)">
              {{ formatNumber(item.top10_special?.oi) }}
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

const getValueColor = (value) => {
  if (value === null || value === undefined) return 'text-gray-900'
  return value >= 0 ? 'text-red-600' : 'text-green-600'
}
</script>

