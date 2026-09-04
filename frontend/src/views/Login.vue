<template>
  <div class="auth-page">
    <div class="auth-card fade-scale-enter-active">
      <div class="auth-header">
        <div class="auth-logo">
          <div class="logo-icon">🤖</div>
        </div>
        <h1 class="auth-title">欢迎回来</h1>
        <p class="auth-sub">登录企业知识问答系统</p>
      </div>

      <el-form :model="form" :rules="rules" ref="formRef" @submit.prevent>
        <el-form-item prop="username">
          <el-input 
            v-model="form.username" 
            placeholder="请输入账号" 
            size="large" 
            :prefix-icon="User"
            clearable
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            show-password
            :prefix-icon="Lock"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item prop="captcha_code">
          <div class="captcha-row">
            <el-input
              v-model="form.captcha_code"
              placeholder="请输入验证码"
              size="large"
              :prefix-icon="Key"
              @keyup.enter="handleLogin"
            />
            <div class="captcha-img-wrapper" @click="refreshCaptcha">
              <img
                :src="captchaImage"
                class="captcha-img"
                alt="验证码"
                title="点击刷新"
              />
              <div v-if="!captchaImage" class="captcha-loading">
                <el-icon class="is-loading"><Loading /></el-icon>
              </div>
            </div>
          </div>
        </el-form-item>
        
        <div class="form-options">
          <el-checkbox v-model="rememberMe">记住密码</el-checkbox>
          <a href="javascript:;" class="forgot-link" @click="handleForgot">忘记密码?</a>
        </div>

        <el-button 
          type="primary" 
          size="large" 
          class="submit gradient-btn" 
          :loading="loading" 
          @click="handleLogin"
        >
          <span v-if="!loading">登 录</span>
          <span v-else>登录中...</span>
        </el-button>
      </el-form>

      <div class="auth-divider">
        <span>还没有账号?</span>
      </div>
      
      <router-link to="/register" class="register-link">
        <el-button size="large" class="register-btn">
          立即注册
        </el-button>
      </router-link>
    </div>
    
    <div class="auth-footer">
      <p>© 2024 企业知识问答系统 · 由 AI 驱动</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Key, Loading } from '@element-plus/icons-vue'
import { getCaptcha, login } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref()

const form = reactive({
  username: '',
  password: '',
  captcha_id: '',
  captcha_code: '',
})

const rememberMe = ref(false)
const captchaImage = ref('')
const loading = ref(false)

// 表单验证规则
const rules = {
  username: [
    { required: true, message: '请输入账号', trigger: 'blur' },
    { min: 3, max: 20, message: '账号长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ],
  captcha_code: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { len: 4, message: '验证码为 4 位', trigger: 'blur' }
  ]
}

// 从本地存储恢复记住的账号密码
function restoreRemembered() {
  const remembered = localStorage.getItem('remembered_user')
  if (remembered) {
    try {
      const { username, password } = JSON.parse(remembered)
      form.username = username || ''
      form.password = password || ''
      rememberMe.value = true
    } catch {
      // 忽略解析错误
    }
  }
}

// 保存或清除记住的账号密码
watch(rememberMe, (val) => {
  if (val) {
    localStorage.setItem('remembered_user', JSON.stringify({
      username: form.username,
      password: form.password
    }))
  } else {
    localStorage.removeItem('remembered_user')
  }
})

async function refreshCaptcha() {
  try {
    const data = await getCaptcha()
    form.captcha_id = data.captcha_id
    captchaImage.value = data.captcha_image
    form.captcha_code = ''
  } catch {
    ElMessage.error('获取验证码失败，请重试')
  }
}

async function handleLogin() {
  // 表单验证
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  loading.value = true
  try {
    const data = await login(form)
    authStore.setLogin(data.username, data.access_token, data.role, data.department_id, data.department_name)
    
    // 保存记住的账号密码
    if (rememberMe.value) {
      localStorage.setItem('remembered_user', JSON.stringify({
        username: form.username,
        password: form.password
      }))
    }
    
    ElMessage.success({
      message: '登录成功',
      duration: 1500
    })
    
    router.push('/chat')
  } catch (error: any) {
    // 登录失败刷新验证码
    refreshCaptcha()
    
    if (error.message?.includes('验证码')) {
      ElMessage.error('验证码错误，请重新输入')
    } else if (error.message?.includes('密码')) {
      ElMessage.error('账号或密码错误')
    } else {
      ElMessage.error(error.message || '登录失败，请重试')
    }
  } finally {
    loading.value = false
  }
}

function handleForgot() {
  ElMessage.info('请联系管理员重置密码')
}

onMounted(() => {
  restoreRemembered()
  refreshCaptcha()
})
</script>

<style scoped>
.auth-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow: hidden;
}

/* 背景装饰 */
.auth-page::before,
.auth-page::after {
  content: '';
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
}

.auth-page::before {
  width: 600px;
  height: 600px;
  top: -200px;
  right: -150px;
  animation: float 6s ease-in-out infinite;
}

.auth-page::after {
  width: 400px;
  height: 400px;
  bottom: -150px;
  left: -100px;
  animation: float 8s ease-in-out infinite reverse;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
  }
  50% {
    transform: translateY(-20px) rotate(5deg);
  }
}

.auth-card {
  width: 420px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 48px 40px 36px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  z-index: 1;
}

.auth-header {
  text-align: center;
  margin-bottom: 32px;
}

.auth-logo {
  margin-bottom: 16px;
}

.logo-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
}

.auth-title {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 8px;
}

.auth-sub {
  color: #6b7280;
  font-size: 15px;
}

/* 表单样式 */
.auth-page :deep(.el-input__wrapper) {
  background: #f9fafb;
  border: 2px solid transparent;
  border-radius: 12px;
  padding: 4px 12px;
  transition: all 0.3s ease;
}

.auth-page :deep(.el-input__wrapper:hover) {
  border-color: #e5e7eb;
}

.auth-page :deep(.el-input__wrapper.is-focus) {
  border-color: #667eea;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.auth-page :deep(.el-form-item) {
  margin-bottom: 20px;
}

.auth-page :deep(.el-form-item__error) {
  padding-top: 4px;
}

.captcha-row {
  display: flex;
  gap: 12px;
  width: 100%;
}

.captcha-img-wrapper {
  position: relative;
  width: 120px;
  height: 44px;
  flex-shrink: 0;
  cursor: pointer;
  border-radius: 12px;
  overflow: hidden;
  background: #f9fafb;
  transition: all 0.3s ease;
}

.captcha-img-wrapper:hover {
  transform: scale(1.02);
}

.captcha-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.captcha-loading {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f9fafb;
}

.form-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.form-options :deep(.el-checkbox__label) {
  font-size: 14px;
  color: #6b7280;
}

.forgot-link {
  font-size: 14px;
  color: #667eea;
  text-decoration: none;
  transition: color 0.2s;
}

.forgot-link:hover {
  color: #764ba2;
}

.submit {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  transition: all 0.3s ease;
}

.submit:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
}

.submit:active {
  transform: translateY(0);
}

.auth-divider {
  display: flex;
  align-items: center;
  margin: 24px 0;
  color: #9ca3af;
  font-size: 14px;
}

.auth-divider::before,
.auth-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: #e5e7eb;
}

.auth-divider span {
  padding: 0 16px;
}

.register-link {
  text-decoration: none;
}

.register-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 12px;
  background: #f3f4f6;
  border: 2px solid #e5e7eb;
  color: #374151;
  transition: all 0.3s ease;
}

.register-btn:hover {
  background: #e5e7eb;
  border-color: #d1d5db;
  transform: translateY(-2px);
}

.auth-footer {
  margin-top: 32px;
  text-align: center;
  color: rgba(255, 255, 255, 0.6);
  font-size: 13px;
}

/* 响应式 */
@media (max-width: 480px) {
  .auth-card {
    width: 100%;
    margin: 16px;
    padding: 32px 24px 28px;
    border-radius: 20px;
  }
  
  .auth-title {
    font-size: 24px;
  }
  
  .logo-icon {
    width: 56px;
    height: 56px;
    font-size: 28px;
  }
}
</style>
