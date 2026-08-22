<template>
  <div class="auth-page">
    <div class="auth-card fade-enter">
      <div class="auth-title">创建账号 🚀</div>
      <div class="auth-sub">注册企业知识问答系统</div>

      <el-form :model="form" @submit.prevent>
        <el-form-item>
          <el-input v-model="form.username" placeholder="账号名称" size="large" :prefix-icon="User" />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码(至少 6 位)"
            size="large"
            show-password
            :prefix-icon="Lock"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.confirm_password"
            type="password"
            placeholder="确认密码"
            size="large"
            show-password
            :prefix-icon="Lock"
            @keyup.enter="handleRegister"
          />
        </el-form-item>
        <el-form-item>
          <div class="captcha-row">
            <el-input
              v-model="form.captcha_code"
              placeholder="验证码"
              size="large"
              :prefix-icon="Key"
              @keyup.enter="handleRegister"
            />
            <img
              :src="captchaImage"
              class="captcha-img"
              alt="验证码"
              title="点击刷新"
              @click="refreshCaptcha"
            />
          </div>
        </el-form-item>
        <el-button type="primary" size="large" class="submit gradient-btn" :loading="loading" @click="handleRegister">
          注 册
        </el-button>
      </el-form>

      <div class="auth-footer">
        已有账号?<router-link to="/login" class="link">返回登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Key } from '@element-plus/icons-vue'
import { getCaptcha, register } from '@/api/auth'

const router = useRouter()

const form = reactive({
  username: '',
  password: '',
  confirm_password: '',
  captcha_id: '',
  captcha_code: '',
})
const captchaImage = ref('')
const loading = ref(false)

async function refreshCaptcha() {
  const data = await getCaptcha()
  form.captcha_id = data.captcha_id
  captchaImage.value = data.captcha_image
  form.captcha_code = ''
}

async function handleRegister() {
  if (!form.username || !form.password || !form.confirm_password || !form.captcha_code) {
    ElMessage.warning('请填写完整信息')
    return
  }
  if (form.password !== form.confirm_password) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  if (form.password.length < 6) {
    ElMessage.warning('密码至少 6 位')
    return
  }
  loading.value = true
  try {
    await register(form)
    ElMessage.success('注册成功,请登录')
    router.push('/login')
  } catch {
    refreshCaptcha()
  } finally {
    loading.value = false
  }
}

onMounted(refreshCaptcha)
</script>

<style scoped>
.auth-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #4f6ef7 0%, #7b5cf0 50%, #b06af5 100%);
  position: relative;
  overflow: hidden;
}
.auth-page::before,
.auth-page::after {
  content: '';
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.12);
}
.auth-page::before {
  width: 380px;
  height: 380px;
  top: -120px;
  right: -80px;
}
.auth-page::after {
  width: 260px;
  height: 260px;
  bottom: -100px;
  left: -60px;
}
.auth-card {
  width: 400px;
  background: #fff;
  border-radius: 18px;
  padding: 42px 40px 32px;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.2);
  z-index: 1;
}
.auth-title {
  font-size: 26px;
  font-weight: 700;
  color: #1f2329;
}
.auth-sub {
  color: #8a919f;
  margin: 8px 0 28px;
  font-size: 14px;
}
.captcha-row {
  display: flex;
  gap: 12px;
  width: 100%;
}
.captcha-img {
  height: 40px;
  width: 120px;
  border-radius: 8px;
  cursor: pointer;
  border: 1px solid #e5e7eb;
  flex-shrink: 0;
}
.submit {
  width: 100%;
  margin-top: 6px;
}
.auth-footer {
  margin-top: 20px;
  text-align: center;
  font-size: 14px;
  color: #8a919f;
}
.link {
  color: #4f6ef7;
  text-decoration: none;
  font-weight: 500;
}
</style>
