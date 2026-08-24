import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import { getMe } from './api/auth'
import { useAuthStore } from './stores/auth'
import './styles/index.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 启动时用后端返回的角色/部门覆盖本地 localStorage(修复旧登录态导致的权限展示错误)
async function syncCurrentUser() {
  if (!localStorage.getItem('token')) return
  try {
    const me = await getMe()
    useAuthStore().syncUser(me.username, me.role, me.department_id, me.department_name)
  } catch {
    // 401 由 axios 拦截器统一处理(清除 token 并跳转登录页)
  }
}
syncCurrentUser()

app.mount('#app')
