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
    {
      path: '/admin',
      component: () => import('@/views/admin/Layout.vue'),
      meta: { requiresAdmin: true },
      children: [
        { path: '', redirect: '/admin/users' },
        { path: 'users', component: () => import('@/views/admin/Users.vue'), meta: { title: '用户管理' } },
        { path: 'departments', component: () => import('@/views/admin/Departments.vue'), meta: { title: '部门管理' } },
        { path: 'permissions', component: () => import('@/views/admin/Permissions.vue'), meta: { title: '权限管理' } },
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
  
  // 检查管理后台权限
  if (to.path.startsWith('/admin')) {
    const role = localStorage.getItem('role')
    if (role !== 'super_admin') {
      return '/'
    }
  }
  
  return true
})

export default router
