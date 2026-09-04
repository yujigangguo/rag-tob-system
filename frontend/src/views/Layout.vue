<template>
  <el-container class="layout">
    <!-- 移动端遮罩 -->
    <div 
      v-if="isMobile && sidebarOpen" 
      class="sidebar-overlay" 
      @click="sidebarOpen = false"
    />
    
    <!-- 侧边栏 -->
    <el-aside 
      :width="isMobile ? '280px' : '240px'" 
      class="aside"
      :class="{ 'sidebar-open': sidebarOpen, 'sidebar-mobile': isMobile }"
    >
      <div class="logo">
        <div class="logo-icon">🤖</div>
        <span class="logo-text">知识问答系统</span>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        router
        class="menu"
        background-color="transparent"
        text-color="rgba(255, 255, 255, 0.7)"
        active-text-color="#ffffff"
        @select="handleMenuSelect"
      >
        <el-menu-item index="/chat">
          <el-icon><ChatDotRound /></el-icon>
          <span>对话</span>
        </el-menu-item>
        <el-menu-item index="/knowledge">
          <el-icon><FolderOpened /></el-icon>
          <span>知识库</span>
        </el-menu-item>
        <el-menu-item v-if="authStore.isSuperAdmin" index="/admin">
          <el-icon><Setting /></el-icon>
          <span>管理后台</span>
        </el-menu-item>
      </el-menu>
      
      <div class="sidebar-footer">
        <div class="version">v1.0.0</div>
      </div>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-button 
            v-if="isMobile" 
            class="menu-btn" 
            :icon="Expand" 
            @click="sidebarOpen = !sidebarOpen"
          />
          <h2 class="header-title">{{ route.meta.title || '企业知识问答系统' }}</h2>
        </div>
        
        <div class="header-right">
          <el-dropdown @command="onCommand" trigger="click">
            <div class="user-info">
              <el-avatar :size="36" class="avatar" :src="authStore.avatarUrl || undefined">
                {{ authStore.displayName.charAt(0).toUpperCase() }}
              </el-avatar>
              <div class="user-detail" v-if="!isMobile">
                <span class="username">{{ authStore.displayName }}</span>
                <el-tag 
                  v-if="authStore.isSuperAdmin" 
                  size="small" 
                  type="danger" 
                  class="role-tag"
                  effect="dark"
                >
                  系统管理员
                </el-tag>
                <el-tag 
                  v-else-if="authStore.role === 'dept_admin'" 
                  size="small" 
                  type="warning" 
                  class="role-tag"
                  effect="dark"
                >
                  部门管理员
                </el-tag>
              </div>
              <el-icon class="arrow-icon"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item disabled v-if="authStore.departmentName">
                  <el-icon><OfficeBuilding /></el-icon>
                  部门: {{ authStore.departmentName }}
                </el-dropdown-item>
                <el-dropdown-item divided command="profile">
                  <el-icon><User /></el-icon>
                  个人设置
                </el-dropdown-item>
                <el-dropdown-item command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <el-main class="main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { 
  ChatDotRound, 
  FolderOpened, 
  Setting, 
  ArrowDown,
  Expand,
  User,
  SwitchButton,
  OfficeBuilding
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const sidebarOpen = ref(false)
const isMobile = ref(false)

const activeMenu = computed(() => route.path)

// 检测屏幕尺寸
function checkMobile() {
  isMobile.value = window.innerWidth < 768
  if (!isMobile.value) {
    sidebarOpen.value = false
  }
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})

function handleMenuSelect() {
  if (isMobile.value) {
    sidebarOpen.value = false
  }
}

function onCommand(cmd: string) {
  if (cmd === 'logout') {
    authStore.logout()
    router.push('/login')
  } else if (cmd === 'profile') {
    // TODO: 跳转到个人设置页面
  }
}
</script>

<style scoped>
.layout {
  height: 100vh;
  overflow: hidden;
}

/* 侧边栏遮罩 */
.sidebar-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 999;
  backdrop-filter: blur(4px);
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* 侧边栏 */
.aside {
  background: linear-gradient(180deg, #1e1e2e 0%, #1a1a2e 100%);
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
  z-index: 1000;
}

.aside.sidebar-mobile {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  transform: translateX(-100%);
  box-shadow: 4px 0 24px rgba(0, 0, 0, 0.2);
}

.aside.sidebar-open {
  transform: translateX(0);
}

.logo {
  height: 72px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.logo-text {
  color: #fff;
  font-weight: 600;
  font-size: 16px;
}

.menu {
  flex: 1;
  border-right: none;
  padding: 16px 12px;
}

.menu :deep(.el-menu-item) {
  border-radius: 12px;
  margin-bottom: 4px;
  height: 48px;
  line-height: 48px;
  transition: all 0.2s ease;
}

.menu :deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.06);
}

.menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.3), rgba(118, 75, 162, 0.3));
  color: #fff;
}

.menu :deep(.el-menu-item .el-icon) {
  font-size: 18px;
  margin-right: 10px;
}

.sidebar-footer {
  padding: 16px 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.version {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.3);
  text-align: center;
}

/* 顶部栏 */
.header {
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  padding: 0 24px;
  height: 64px;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.menu-btn {
  border: none;
  background: transparent;
  font-size: 20px;
  color: #374151;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a2e;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: 12px;
  transition: all 0.2s ease;
}

.user-info:hover {
  background: #f3f4f6;
}

.avatar {
  background: linear-gradient(135deg, #667eea, #764ba2);
  font-weight: 600;
}

.user-detail {
  display: flex;
  align-items: center;
  gap: 8px;
}

.username {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.role-tag {
  border: none;
}

.arrow-icon {
  font-size: 12px;
  color: #9ca3af;
  transition: transform 0.2s ease;
}

.user-info:hover .arrow-icon {
  transform: rotate(180deg);
}

/* 主内容区 */
.main {
  padding: 20px;
  overflow: auto;
  background: #f5f7fb;
}

/* 路由过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* 响应式 */
@media (max-width: 768px) {
  .header {
    padding: 0 16px;
  }
  
  .header-title {
    font-size: 16px;
  }
  
  .main {
    padding: 12px;
  }
}
</style>
