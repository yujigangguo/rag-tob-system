import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: () => import('@/views/Login.vue'), meta: { title: '登录' } },
    { path: '/register', component: () => import('@/views/Register.vue'), meta: { title: '注册' } },
    {
      path: '/',
      component: () => import('@/views/Layout.vue'),
      children: [
        { path: '', redirect: '/chat' },
        { path: 'chat', component: () => import('@/views/Chat.vue'), meta: { title: '对话' } },
        { path: 'knowledge', component: () => import('@/views/KnowledgeBaseList.vue'), meta: { title: '知识库' } },
        { path: 'knowledge/:id', component: () => import('@/views/KnowledgeBaseDetail.vue'), meta: { title: '知识库详情' } },
      ],
    },
  ],
})

router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  if (!token && to.path !== '/login' && to.path !== '/register') {
    return '/login'
  }
  if (token && (to.path === '/login' || to.path === '/register')) {
    return '/'
  }
  return true
})

export default router
