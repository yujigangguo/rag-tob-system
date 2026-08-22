import http from './index'

export interface CaptchaData {
  captcha_id: string
  captcha_image: string
}

export function getCaptcha(): Promise<CaptchaData> {
  return http.get('/auth/captcha').then((r) => r.data)
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
}): Promise<{ access_token: string; token_type: string; username: string }> {
  return http.post('/auth/login', data).then((r) => r.data)
}
