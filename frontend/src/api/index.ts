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
