<template>
  <div class="permissions-container">
    <!-- 角色列表 -->
    <el-card class="card">
      <template #header>
        <div class="card-header">
          <span>系统角色</span>
        </div>
      </template>
      <el-table :data="roles" v-loading="loading" stripe>
        <el-table-column prop="value" label="角色标识" width="150" />
        <el-table-column prop="label" label="角色名称" width="150" />
        <el-table-column prop="description" label="角色描述" />
      </el-table>
    </el-card>

    <!-- 权限矩阵 -->
    <el-card class="card">
      <template #header>
        <div class="card-header">
          <span>权限矩阵</span>
        </div>
      </template>
      <el-table :data="permissionMatrix" v-loading="loading" stripe border>
        <el-table-column prop="permission" label="权限项" width="200" />
        <el-table-column label="超级管理员" width="150" align="center">
          <template #default="{ row }">
            <el-tag :type="row.super_admin ? 'success' : 'danger'">
              {{ row.super_admin ? '✓ 允许' : '✗ 禁止' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="部门管理员" width="150" align="center">
          <template #default="{ row }">
            <el-tag :type="getPermissionType(row.dept_admin)">
              {{ getPermissionLabel(row.dept_admin) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="普通员工" width="150" align="center">
          <template #default="{ row }">
            <el-tag :type="getPermissionType(row.employee)">
              {{ getPermissionLabel(row.employee) }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 权限说明 -->
    <el-card class="card">
      <template #header>
        <div class="card-header">
          <span>权限说明</span>
        </div>
      </template>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="超级管理员">
          系统管理员，拥有所有权限。可以管理所有用户、部门和知识库。
        </el-descriptions-item>
        <el-descriptions-item label="部门管理员">
          部门管理员，可以管理本部门的用户和知识库。不能访问其他部门的数据。
        </el-descriptions-item>
        <el-descriptions-item label="普通员工">
          普通员工，只能查看本部门的知识库，不能管理用户和部门。
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getRoles, getPermissions } from '@/api'

interface Role {
  value: string
  label: string
  description: string
}

interface Permissions {
  roles: Role[]
  permissions: {
    [key: string]: {
      super_admin: boolean | string
      dept_admin: boolean | string
      employee: boolean | string
    }
  }
}

// 角色数据
const roles = ref<Role[]>([])
const permissions = ref<Permissions | null>(null)
const loading = ref(false)

// 权限矩阵数据
const permissionMatrix = computed(() => {
  if (!permissions.value) return []
  
  const matrix = []
  const permData = permissions.value.permissions
  
  // 权限项映射
  const permissionLabels: { [key: string]: string } = {
    user_management: '用户管理',
    department_management: '部门管理',
    knowledge_base_management: '知识库管理',
    knowledge_base_view: '知识库查看',
  }
  
  for (const [key, value] of Object.entries(permData)) {
    matrix.push({
      permission: permissionLabels[key] || key,
      super_admin: value.super_admin,
      dept_admin: value.dept_admin,
      employee: value.employee,
    })
  }
  
  return matrix
})

// 获取角色列表
const fetchRoles = async () => {
  try {
    const response = await getRoles()
    roles.value = response.data
  } catch (error) {
    console.error('获取角色列表失败:', error)
  }
}

// 获取权限配置
const fetchPermissions = async () => {
  loading.value = true
  try {
    const response = await getPermissions()
    permissions.value = response.data
  } catch (error) {
    console.error('获取权限配置失败:', error)
  } finally {
    loading.value = false
  }
}

// 获取权限标签类型
const getPermissionType = (value: boolean | string) => {
  if (value === true || value === 'all') return 'success'
  if (value === 'department') return 'warning'
  return 'danger'
}

// 获取权限标签文本
const getPermissionLabel = (value: boolean | string) => {
  if (value === true) return '✓ 允许'
  if (value === 'all') return '✓ 所有'
  if (value === 'department') return '✓ 本部门'
  return '✗ 禁止'
}

// 初始化
onMounted(() => {
  fetchRoles()
  fetchPermissions()
})
</script>

<style scoped>
.permissions-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card {
  margin-bottom: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}
</style>