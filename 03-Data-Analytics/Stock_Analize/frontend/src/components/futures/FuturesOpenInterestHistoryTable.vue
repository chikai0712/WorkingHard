<template>
  <div class="bg-white rounded-lg shadow">
    <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
      <h2 class="text-lg font-semibold text-gray-900">近7日台股期貨未平倉</h2>
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
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">自營</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">總計</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="item in data" :key="item.date" class="hover:bg-gray-50">
            <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-900">{{ formatDate(item.date) }}</td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-right">
              <div :class="getOIColor(item.foreign?.oi)">
                {{ formatNumber(item.foreign?.oi) }}
              </div>
              <div class="text-xs mt-1" :class="getChangeColor(item.foreign?.oi_change)">
                {{ formatChange(item.foreign?.oi_change) }}
              </div>
            </td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-right">
              <div :class="getOIColor(item.trust?.oi)">
                {{ formatNumber(item.trust?.oi) }}
              </div>
              <div class="text-xs mt-1" :class="getChangeColor(item.trust?.oi_change)">
                {{ formatChange(item.trust?.oi_change) }}
              </div>
            </td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-right">
              <div :class="getOIColor(item.dealer?.oi)">
                {{ formatNumber(item.dealer?.oi) }}
              </div>
              <div class="text-xs mt-1" :class="getChangeColor(item.dealer?.oi_change)">
                {{ formatChange(item.dealer?.oi_change) }}
              </div>
            </td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-right font-semibold" :class="getOIColor(calculateTotal(item))">
              {{ formatNumber(calculateTotal(item)) }}
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

const calculateTotal = (item) => {
  const foreign = item.foreign?.oi || 0
  const trust = item.trust?.oi || 0
  const dealer = item.dealer?.oi || 0
  return foreign + trust + dealer
}

const getOIColor = (oi) => {
  if (oi === null || oi === undefined) return 'text-gray-900'
  return oi >= 0 ? 'text-red-600' : 'text-green-600'
}

const getChangeColor = (change) => {
  if (change === null || change === undefined || change === 0) return 'text-gray-500'
  return change >= 0 ? 'text-red-600' : 'text-green-600'
}
</script>

