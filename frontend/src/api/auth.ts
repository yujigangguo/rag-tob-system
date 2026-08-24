import http from './index'
import type { LoginResult, Role } from '@/types'

export interface CaptchaData {
  captcha_id: string
  captcha_image: string
}

export function getCaptcha(): Promise<CaptchaData> {
  return http.get('/auth/captcha').then((r) => r.data)
}

export function getMe(): Promise<{
  id: number
  username: string
  role: Role
  department_id: number | null
  department_name: string | null
}> {
  return http.get('/auth/me').then((r) => r.data)
}

export function register(data: {
  username: string
  password: string
  confirm_password: string
  captcha_id: string
  captcha_code: string
}) {
  return http.post('/auth/register', data).then((r) => r.data)
}

export function login(data: {
  username: string
  password: string
  captcha_id: string
  captcha_code: string
}): Promise<LoginResult> {
  return http.post('/auth/login', data).then((r) => r.data)
}
