import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import StockDetail from '../views/StockDetail.vue'
import FuturesDashboard from '../views/FuturesDashboard.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/stock/:symbol',
    name: 'StockDetail',
    component: StockDetail,
    props: true
  },
  {
    path: '/futures',
    name: 'FuturesDashboard',
    component: FuturesDashboard
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
