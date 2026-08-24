import { defineStore } from 'pinia'
import type { Role } from '@/types'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    username: localStorage.getItem('username') || '',
    role: (localStorage.getItem('role') as Role) || 'employee',
    departmentId: Number(localStorage.getItem('departmentId')) || null,
    departmentName: localStorage.getItem('departmentName') || '',
  }),
  getters: {
    isAdmin(state): boolean {
      return state.role === 'super_admin' || state.role === 'dept_admin'
    },
    isSuperAdmin(state): boolean {
      return state.role === 'super_admin'
    },
  },
  actions: {
    setLogin(username: string, token: string, role: Role, departmentId: number | null, departmentName: string | null) {
      this.username = username
      this.role = role
      this.departmentId = departmentId
      this.departmentName = departmentName || ''
      localStorage.setItem('username', username)
      localStorage.setItem('token', token)
      localStorage.setItem('role', role)
      localStorage.setItem('departmentId', String(departmentId ?? ''))
      localStorage.setItem('departmentName', this.departmentName)
    },
    // 启动时从后端 /auth/me 同步角色与部门(修复旧登录态 localStorage 缺失导致的权限展示错误)
    syncUser(username: string, role: Role, departmentId: number | null, departmentName: string | null) {
      this.username = username
      this.role = role
      this.departmentId = departmentId
      this.departmentName = departmentName || ''
      localStorage.setItem('username', username)
      localStorage.setItem('role', role)
      localStorage.setItem('departmentId', String(departmentId ?? ''))
      localStorage.setItem('departmentName', this.departmentName)
    },
    logout() {
      this.username = ''
      this.role = 'employee'
      this.departmentId = null
      this.departmentName = ''
      localStorage.removeItem('username')
      localStorage.removeItem('token')
      localStorage.removeItem('role')
      localStorage.removeItem('departmentId')
      localStorage.removeItem('departmentName')
    },
  },
})
