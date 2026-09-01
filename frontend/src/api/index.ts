import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// axios 实例,自动带 token
const http = axios.create({
  baseURL: '/api',
  timeout: 120000,
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (resp) => resp,
  (error) => {
    const status = error.response?.status
    const detail = error.response?.data?.detail
    if (status === 401) {
      localStorage.removeItem('token')
      ElMessage.error('登录已过期,请重新登录')
      router.push('/login')
    } else if (detail) {
      ElMessage.error(typeof detail === 'string' ? detail : '请求失败')
    } else {
      ElMessage.error('网络错误,请稍后重试')
    }
    return Promise.reject(error)
  },
)

export default http

// ==================== 管理后台 API ====================

// 用户管理
export const getUsers = (params: {
  page?: number
  page_size?: number
  search?: string
  role?: string
  department_id?: number
}) => http.get('/admin/users', { params })

export const getUser = (userId: number) => http.get(`/admin/users/${userId}`)

export const updateUser = (userId: number, data: {
  username?: string
  role?: string
  department_id?: number
}) => http.put(`/admin/users/${userId}`, data)

export const deleteUser = (userId: number) => http.delete(`/admin/users/${userId}`)

export const updateUserRole = (userId: number, role: string) => 
  http.put(`/admin/users/${userId}/role`, { role })

export const updateUserDepartment = (userId: number, departmentId: number | null) => 
  http.put(`/admin/users/${userId}/department`, { department_id: departmentId })

// 部门管理
export const getDepartments = () => http.get('/admin/departments')

export const createDepartment = (name: string) => http.post('/admin/departments', { name })

export const updateDepartment = (departmentId: number, name: string) => 
  http.put(`/admin/departments/${departmentId}`, { name })

export const deleteDepartment = (departmentId: number) => http.delete(`/admin/departments/${departmentId}`)

// 权限管理
export const getRoles = () => http.get('/admin/roles')

export const getPermissions = () => http.get('/admin/permissions')
