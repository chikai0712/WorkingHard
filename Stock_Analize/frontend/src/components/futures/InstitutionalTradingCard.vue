<template>
  <div class="bg-white rounded-lg shadow">
    <div class="px-6 py-4 border-b border-gray-200">
      <h2 class="text-lg font-semibold text-gray-900">三大法人買賣超</h2>
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
    
    <div v-else class="overflow-x-auto">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">法人類型</th>
            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">買進(億)</th>
            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">賣出(億)</th>
            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">淨買賣超(億)</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <!-- 外資 -->
          <tr>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">外資</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
              {{ formatNumber(data.foreign?.buy) }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
              {{ formatNumber(data.foreign?.sell) }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-right font-semibold" :class="getNetColor(data.foreign?.net)">
              {{ formatChange(data.foreign?.net) }}
            </td>
          </tr>
          
          <!-- 投信 -->
          <tr>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">投信</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
              {{ formatNumber(data.trust?.buy) }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
              {{ formatNumber(data.trust?.sell) }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-right font-semibold" :class="getNetColor(data.trust?.net)">
              {{ formatChange(data.trust?.net) }}
            </td>
          </tr>
          
          <!-- 自營商 -->
          <tr>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">自營商</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
              {{ formatNumber(data.dealer?.buy) }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
              {{ formatNumber(data.dealer?.sell) }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-right font-semibold" :class="getNetColor(data.dealer?.net)">
              {{ formatChange(data.dealer?.net) }}
            </td>
          </tr>
          
          <!-- 自營商細分 -->
          <tr v-if="data.dealer?.self_buy !== null" class="bg-gray-50">
            <td class="px-6 py-3 text-sm text-gray-600 pl-12">自營(自買)</td>
            <td class="px-6 py-3 text-sm text-gray-600 text-right">
              {{ formatNumber(data.dealer?.self_buy) }}
            </td>
            <td class="px-6 py-3 text-sm text-gray-600 text-right">
              {{ formatNumber(data.dealer?.self_sell) }}
            </td>
            <td class="px-6 py-3 text-sm text-right font-medium" :class="getNetColor(data.dealer?.self_net)">
              {{ formatChange(data.dealer?.self_net) }}
            </td>
          </tr>
          
          <tr v-if="data.dealer?.hedge_buy !== null" class="bg-gray-50">
            <td class="px-6 py-3 text-sm text-gray-600 pl-12">自營(避險)</td>
            <td class="px-6 py-3 text-sm text-gray-600 text-right">
              {{ formatNumber(data.dealer?.hedge_buy) }}
            </td>
            <td class="px-6 py-3 text-sm text-gray-600 text-right">
              {{ formatNumber(data.dealer?.hedge_sell) }}
            </td>
            <td class="px-6 py-3 text-sm text-right font-medium" :class="getNetColor(data.dealer?.hedge_net)">
              {{ formatChange(data.dealer?.hedge_net) }}
            </td>
          </tr>
          
          <!-- 合計 -->
          <tr class="bg-gray-100 border-t-2 border-gray-300">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900">三大法人合計</td>
            <td colspan="2"></td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-right font-bold" :class="getNetColor(data.total_net)">
              {{ formatChange(data.total_net) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
defineProps({
  data: Object,
  loading: Boolean
})

const formatNumber = (num) => {
  if (num === null || num === undefined || num === 0) return '-'
  return new Intl.NumberFormat('zh-TW', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(num)
}

const formatChange = (change) => {
  if (change === null || change === undefined) return '-'
  const sign = change >= 0 ? '+' : ''
  return `${sign}${change.toFixed(2)}`
}

const getNetColor = (net) => {
  if (net === null || net === undefined) return 'text-gray-900'
  return net >= 0 ? 'text-red-600' : 'text-green-600'
}
</script>

