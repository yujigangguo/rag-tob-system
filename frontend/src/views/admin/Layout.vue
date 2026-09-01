<template>
  <el-container class="admin-layout">
    <el-aside width="220px" class="aside">
      <div class="logo">
        <span class="logo-dot"></span>
        管理后台
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        class="menu"
        background-color="transparent"
        text-color="#aab2c5"
        active-text-color="#ffffff"
      >
        <el-menu-item index="/admin/users">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/departments">
          <el-icon><OfficeBuilding /></el-icon>
          <span>部门管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/permissions">
          <el-icon><Lock /></el-icon>
          <span>权限管理</span>
        </el-menu-item>
        <el-divider />
        <el-menu-item index="/">
          <el-icon><Back /></el-icon>
          <span>返回主系统</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-title">{{ route.meta.title || '管理后台' }}</div>
        <el-dropdown @command="onCommand">
          <span class="user">
            <el-avatar :size="30" class="avatar">{{ authStore.username.charAt(0).toUpperCase() }}</el-avatar>
            <span class="username">{{ authStore.username }}</span>
            <el-tag size="small" type="danger" class="role-tag">超级管理员</el-tag>
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item disabled v-if="authStore.departmentName">
                部门:{{ authStore.departmentName }}
              </el-dropdown-item>
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
import { User, OfficeBuilding, Lock, Back, ArrowDown } from '@element-plus/icons-vue'

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
.admin-layout {
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
  background: linear-gradient(135deg, #e74c3c, #c0392b);
  box-shadow: 0 0 12px rgba(231, 76, 60, 0.8);
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
  background: linear-gradient(135deg, #e74c3c, #c0392b);
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
  background: linear-gradient(135deg, #e74c3c, #c0392b);
}
.username {
  font-size: 14px;
}
.role-tag {
  margin: 0 2px;
}
.main {
  padding: 20px;
  overflow: auto;
}
</style>