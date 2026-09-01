<template>
  <div class="departments-container">
    <!-- 操作栏 -->
    <el-card class="action-card">
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon>
        创建部门
      </el-button>
    </el-card>

    <!-- 部门列表 -->
    <el-card class="table-card">
      <el-table :data="departments" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="部门名称" width="200" />
        <el-table-column prop="user_count" label="用户数量" width="120" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑部门对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑部门' : '创建部门'"
      width="400px"
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="部门名称" required>
          <el-input
            v-model="form.name"
            placeholder="请输入部门名称"
            maxlength="64"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">
          {{ isEdit ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  getDepartments,
  createDepartment,
  updateDepartment,
  deleteDepartment,
} from '@/api'

interface Department {
  id: number
  name: string
  user_count: number
  created_at: string
}

// 列表数据
const departments = ref<Department[]>([])
const loading = ref(false)

// 对话框状态
const dialogVisible = ref(false)
const isEdit = ref(false)
const form = ref({
  id: 0,
  name: '',
})

// 提交状态
const submitting = ref(false)

// 获取部门列表
const fetchDepartments = async () => {
  loading.value = true
  try {
    const response = await getDepartments()
    departments.value = response.data
  } catch (error) {
    console.error('获取部门列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 创建部门
const handleCreate = () => {
  isEdit.value = false
  form.value = {
    id: 0,
    name: '',
  }
  dialogVisible.value = true
}

// 编辑部门
const handleEdit = (department: Department) => {
  isEdit.value = true
  form.value = {
    id: department.id,
    name: department.name,
  }
  dialogVisible.value = true
}

// 提交表单
const submitForm = async () => {
  if (!form.value.name.trim()) {
    ElMessage.warning('请输入部门名称')
    return
  }

  submitting.value = true
  try {
    if (isEdit.value) {
      await updateDepartment(form.value.id, form.value.name.trim())
      ElMessage.success('部门更新成功')
    } else {
      await createDepartment(form.value.name.trim())
      ElMessage.success('部门创建成功')
    }
    dialogVisible.value = false
    fetchDepartments()
  } catch (error) {
    console.error('操作失败:', error)
  } finally {
    submitting.value = false
  }
}

// 删除部门
const handleDelete = async (department: Department) => {
  if (department.user_count > 0) {
    ElMessage.warning('该部门下还有用户，无法删除')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除部门 "${department.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await deleteDepartment(department.id)
    ElMessage.success('部门删除成功')
    fetchDepartments()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除部门失败:', error)
    }
  }
}

// 格式化日期
const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

// 初始化
onMounted(() => {
  fetchDepartments()
})
</script>

<style scoped>
.departments-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.action-card {
  margin-bottom: 0;
}

.table-card {
  margin-bottom: 0;
}
</style>