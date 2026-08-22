<template>
  <el-container class="layout">
    <el-aside width="220px" class="aside">
      <div class="logo">
        <span class="logo-dot"></span>
        知识问答系统
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        class="menu"
        background-color="transparent"
        text-color="#aab2c5"
        active-text-color="#ffffff"
      >
        <el-menu-item index="/chat">
          <el-icon><ChatDotRound /></el-icon>
          <span>对话</span>
        </el-menu-item>
        <el-menu-item index="/knowledge">
          <el-icon><FolderOpened /></el-icon>
          <span>知识库</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-title">{{ route.meta.title || '企业知识问答系统' }}</div>
        <el-dropdown @command="onCommand">
          <span class="user">
            <el-avatar :size="30" class="avatar">{{ authStore.username.charAt(0).toUpperCase() }}</el-avatar>
            <span class="username">{{ authStore.username }}</span>
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)

function onCommand(cmd: string) {
  if (cmd === 'logout') {
    authStore.logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.layout {
  height: 100vh;
}
.aside {
  background: linear-gradient(180deg, #232a3d 0%, #1a2030 100%);
  display: flex;
  flex-direction: column;
}
.logo {
  height: 64px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 20px;
  color: #fff;
  font-weight: 600;
  font-size: 17px;
}
.logo-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: linear-gradient(135deg, #4f6ef7, #7b5cf0);
  box-shadow: 0 0 12px rgba(79, 110, 247, 0.8);
}
.menu {
  border-right: none;
  padding: 10px 8px;
}
.menu :deep(.el-menu-item) {
  border-radius: 10px;
  margin-bottom: 6px;
}
.menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, #4f6ef7, #7b5cf0);
}
.header {
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}
.header-title {
  font-size: 16px;
  font-weight: 600;
}
.user {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  outline: none;
}
.avatar {
  background: linear-gradient(135deg, #4f6ef7, #7b5cf0);
}
.username {
  font-size: 14px;
}
.main {
  padding: 20px;
  overflow: auto;
}
</style>
