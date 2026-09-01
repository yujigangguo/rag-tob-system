<template>
  <div class="users-container">
    <!-- 搜索和筛选 -->
    <el-card class="filter-card">
      <el-row :gutter="20">
        <el-col :span="8">
          <el-input
            v-model="searchQuery"
            placeholder="搜索用户名"
            clearable
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="6">
          <el-select v-model="filterRole" placeholder="选择角色" clearable>
            <el-option
              v-for="role in roles"
              :key="role.value"
              :label="role.label"
              :value="role.value"
            />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="filterDepartment" placeholder="选择部门" clearable>
            <el-option
              v-for="dept in departments"
              :key="dept.id"
              :label="dept.name"
              :value="dept.id"
            />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 用户列表 -->
    <el-card class="table-card">
      <el-table :data="users" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="role" label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="getRoleTagType(row.role)">
              {{ getRoleLabel(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="department_name" label="部门" width="150">
          <template #default="{ row }">
            {{ row.department_name || '未分配' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="300" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="warning" @click="handleAssignRole(row)">
              分配角色
            </el-button>
            <el-button size="small" type="success" @click="handleAssignDepartment(row)">
              分配部门
            </el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        class="pagination"
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </el-card>

    <!-- 编辑用户对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑用户" width="500px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="用户名">
          <el-input v-model="editForm.username" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="editForm.role" placeholder="选择角色">
            <el-option
              v-for="role in roles"
              :key="role.value"
              :label="role.label"
              :value="role.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="部门">
          <el-select v-model="editForm.department_id" placeholder="选择部门" clearable>
            <el-option
              v-for="dept in departments"
              :key="dept.id"
              :label="dept.name"
              :value="dept.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEdit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- 分配角色对话框 -->
    <el-dialog v-model="roleDialogVisible" title="分配角色" width="400px">
      <el-form :model="roleForm" label-width="80px">
        <el-form-item label="用户">
          <el-input :value="roleForm.username" disabled />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="roleForm.role" placeholder="选择角色">
            <el-option
              v-for="role in roles"
              :key="role.value"
              :label="role.label"
              :value="role.value"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="roleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitRole" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- 分配部门对话框 -->
    <el-dialog v-model="departmentDialogVisible" title="分配部门" width="400px">
      <el-form :model="departmentForm" label-width="80px">
        <el-form-item label="用户">
          <el-input :value="departmentForm.username" disabled />
        </el-form-item>
        <el-form-item label="部门">
          <el-select v-model="departmentForm.department_id" placeholder="选择部门" clearable>
            <el-option
              v-for="dept in departments"
              :key="dept.id"
              :label="dept.name"
              :value="dept.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="departmentDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitDepartment" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import {
  getUsers,
  updateUser,
  deleteUser,
  updateUserRole,
  updateUserDepartment,
  getRoles,
  getDepartments,
} from '@/api'

interface User {
  id: number
  username: string
  role: string
  department_id: number | null
  department_name: string | null
  created_at: string
}

interface Role {
  value: string
  label: string
  description: string
}

interface Department {
  id: number
  name: string
  user_count: number
}

// 列表数据
const users = ref<User[]>([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 筛选条件
const searchQuery = ref('')
const filterRole = ref('')
const filterDepartment = ref<number | undefined>(undefined)

// 角色和部门数据
const roles = ref<Role[]>([])
const departments = ref<Department[]>([])

// 编辑对话框
const editDialogVisible = ref(false)
const editForm = ref({
  id: 0,
  username: '',
  role: '',
  department_id: null as number | null,
})

// 分配角色对话框
const roleDialogVisible = ref(false)
const roleForm = ref({
  id: 0,
  username: '',
  role: '',
})

// 分配部门对话框
const departmentDialogVisible = ref(false)
const departmentForm = ref({
  id: 0,
  username: '',
  department_id: null as number | null,
})

// 提交状态
const submitting = ref(false)

// 获取用户列表
const fetchUsers = async () => {
  loading.value = true
  try {
    const params: any = {
      page: currentPage.value,
      page_size: pageSize.value,
    }
    if (searchQuery.value) params.search = searchQuery.value
    if (filterRole.value) params.role = filterRole.value
    if (filterDepartment.value) params.department_id = filterDepartment.value

    const response = await getUsers(params)
    users.value = response.data.items
    total.value = response.data.total
  } catch (error) {
    console.error('获取用户列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 获取角色列表
const fetchRoles = async () => {
  try {
    const response = await getRoles()
    roles.value = response.data
  } catch (error) {
    console.error('获取角色列表失败:', error)
  }
}

// 获取部门列表
const fetchDepartments = async () => {
  try {
    const response = await getDepartments()
    departments.value = response.data
  } catch (error) {
    console.error('获取部门列表失败:', error)
  }
}

// 搜索
const handleSearch = () => {
  currentPage.value = 1
  fetchUsers()
}

// 分页大小变化
const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  fetchUsers()
}

// 当前页变化
const handleCurrentChange = (page: number) => {
  currentPage.value = page
  fetchUsers()
}

// 编辑用户
const handleEdit = (user: User) => {
  editForm.value = {
    id: user.id,
    username: user.username,
    role: user.role,
    department_id: user.department_id,
  }
  editDialogVisible.value = true
}

// 提交编辑
const submitEdit = async () => {
  submitting.value = true
  try {
    await updateUser(editForm.value.id, {
      username: editForm.value.username,
      role: editForm.value.role,
      department_id: editForm.value.department_id,
    })
    ElMessage.success('用户信息更新成功')
    editDialogVisible.value = false
    fetchUsers()
  } catch (error) {
    console.error('更新用户失败:', error)
  } finally {
    submitting.value = false
  }
}

// 分配角色
const handleAssignRole = (user: User) => {
  roleForm.value = {
    id: user.id,
    username: user.username,
    role: user.role,
  }
  roleDialogVisible.value = true
}

// 提交角色分配
const submitRole = async () => {
  submitting.value = true
  try {
    await updateUserRole(roleForm.value.id, roleForm.value.role)
    ElMessage.success('角色分配成功')
    roleDialogVisible.value = false
    fetchUsers()
  } catch (error) {
    console.error('分配角色失败:', error)
  } finally {
    submitting.value = false
  }
}

// 分配部门
const handleAssignDepartment = (user: User) => {
  departmentForm.value = {
    id: user.id,
    username: user.username,
    department_id: user.department_id,
  }
  departmentDialogVisible.value = true
}

// 提交部门分配
const submitDepartment = async () => {
  submitting.value = true
  try {
    await updateUserDepartment(departmentForm.value.id, departmentForm.value.department_id)
    ElMessage.success('部门分配成功')
    departmentDialogVisible.value = false
    fetchUsers()
  } catch (error) {
    console.error('分配部门失败:', error)
  } finally {
    submitting.value = false
  }
}

// 删除用户
const handleDelete = async (user: User) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${user.username}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await deleteUser(user.id)
    ElMessage.success('用户删除成功')
    fetchUsers()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除用户失败:', error)
    }
  }
}

// 获取角色标签类型
const getRoleTagType = (role: string) => {
  switch (role) {
    case 'super_admin':
      return 'danger'
    case 'dept_admin':
      return 'warning'
    case 'employee':
      return 'info'
    default:
      return 'info'
  }
}

// 获取角色标签文本
const getRoleLabel = (role: string) => {
  const found = roles.value.find(r => r.value === role)
  return found ? found.label : role
}

// 格式化日期
const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

// 初始化
onMounted(() => {
  fetchUsers()
  fetchRoles()
  fetchDepartments()
})
</script>

<style scoped>
.users-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.filter-card {
  margin-bottom: 0;
}

.table-card {
  margin-bottom: 0;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>