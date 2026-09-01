import { defineStore } from 'pinia'
import type { Role } from '@/types'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    username: localStorage.getItem('username') || '',
    role: (localStorage.getItem('role') as Role) || 'employee',
    departmentId: Number(localStorage.getItem('departmentId')) || null,
    departmentName: localStorage.getItem('departmentName') || '',
    nickname: localStorage.getItem('nickname') || '',
    email: localStorage.getItem('email') || '',
    avatarUrl: localStorage.getItem('avatarUrl') || '',
  }),
  getters: {
    isAdmin(state): boolean {
      return state.role === 'super_admin' || state.role === 'dept_admin'
    },
    isSuperAdmin(state): boolean {
      return state.role === 'super_admin'
    },
    displayName(state): string {
      return state.nickname || state.username
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
    syncUser(data: {
      username: string
      role: Role
      departmentId: number | null
      departmentName: string | null
      nickname?: string | null
      email?: string | null
      avatarUrl?: string | null
    }) {
      this.username = data.username
      this.role = data.role
      this.departmentId = data.departmentId
      this.departmentName = data.departmentName || ''
      this.nickname = data.nickname || ''
      this.email = data.email || ''
      this.avatarUrl = data.avatarUrl || ''
      localStorage.setItem('username', data.username)
      localStorage.setItem('role', data.role)
      localStorage.setItem('departmentId', String(data.departmentId ?? ''))
      localStorage.setItem('departmentName', this.departmentName)
      localStorage.setItem('nickname', this.nickname)
      localStorage.setItem('email', this.email)
      localStorage.setItem('avatarUrl', this.avatarUrl)
    },
    logout() {
      this.username = ''
      this.role = 'employee'
      this.departmentId = null
      this.departmentName = ''
      this.nickname = ''
      this.email = ''
      this.avatarUrl = ''
      localStorage.removeItem('username')
      localStorage.removeItem('token')
      localStorage.removeItem('role')
      localStorage.removeItem('departmentId')
      localStorage.removeItem('departmentName')
      localStorage.removeItem('nickname')
      localStorage.removeItem('email')
      localStorage.removeItem('avatarUrl')
    },
  },
})
