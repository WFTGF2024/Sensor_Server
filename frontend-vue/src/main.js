import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import { useUserStore } from '@/stores/user'
import '@/assets/css/style.css'
import '@/assets/css/responsive.css'

const app = createApp(App)
const pinia = createPinia()

// 注册所有 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(pinia)
app.use(router)
app.use(ElementPlus, {
  locale: zhCn
})

// 在应用挂载前尝试恢复用户登录状态
const userStore = useUserStore()
userStore.fetchUserInfo().catch(() => {
  // 未登录，静默失败，不做任何处理
  console.log('未检测到登录状态')
})

app.mount('#app')
