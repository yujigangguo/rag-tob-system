<template>
  <div class="kb-page fade-enter">
    <div class="toolbar">
      <div>
        <h2>知识库管理</h2>
        <p class="sub">创建多个知识库,每个知识库可上传多个文档</p>
      </div>
      <el-button v-if="isAdmin" type="primary" class="gradient-btn" :icon="Plus" @click="openCreate">创建知识库</el-button>
    </div>

    <el-empty v-if="kbs.length === 0" description="还没有知识库,请联系管理员创建" />

    <el-row :gutter="16">
      <el-col v-for="kb in kbs" :key="kb.id" :xs="24" :sm="12" :md="8">
        <el-card class="kb-card hover-lift" shadow="hover" @click="goDetail(kb.id)">
          <div class="kb-head">
            <div class="kb-icon">📚</div>
            <div>
              <div class="kb-name">{{ kb.name }}</div>
              <div class="kb-time">{{ kb.created_at.slice(0, 10) }} · {{ deptName(kb.department_id) }}</div>
            </div>
          </div>
          <div class="kb-desc">{{ kb.description || '暂无描述' }}</div>
          <div class="kb-meta">
            <el-tag size="small" :type="kb.retrieval_type === 'hybrid' ? 'primary' : 'info'">
              {{ kb.retrieval_type === 'hybrid' ? '混合检索' : '稠密检索' }}
            </el-tag>
            <span class="doc-count">文档 {{ kb.doc_count }} 个</span>
          </div>
          <div class="kb-actions">
            <el-button text type="primary" @click.stop="goDetail(kb.id)">查看</el-button>
            <el-button v-if="isAdmin" text type="danger" @click.stop="remove(kb)">删除</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="dialog" title="创建知识库" width="480px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="如:产品手册库" maxlength="128" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="可选" />
        </el-form-item>
        <el-form-item label="所属部门" required>
          <el-select v-model="form.department_id" placeholder="选择部门" style="width: 100%">
            <el-option v-for="d in deptOptions" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="检索方式">
          <el-radio-group v-model="form.retrieval_type">
            <el-radio value="hybrid">混合检索</el-radio>
            <el-radio value="dense">稠密向量</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="切块大小">
          <el-input-number v-model="form.chunk_size" :min="50" :max="4000" :step="50" />
        </el-form-item>
        <el-form-item label="重叠大小">
          <el-input-number v-model="form.chunk_overlap" :min="0" :max="1000" :step="10" />
        </el-form-item>
        <el-form-item label="父块大小">
          <el-input-number v-model="form.parent_chunk_size" :min="100" :max="8000" :step="100" />
        </el-form-item>
        <div class="form-tip">父子分块:子块(切块大小)用于检索,父块(父块大小)命中后作为完整上下文返回给大模型</div>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" class="gradient-btn" :loading="creating" @click="create">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { createKnowledgeBase, deleteKnowledgeBase, listDepartments, listKnowledgeBases } from '@/api/knowledgeBase'
import { useAuthStore } from '@/stores/auth'
import type { Department, KnowledgeBase } from '@/types'

const router = useRouter()
const authStore = useAuthStore()
const kbs = ref<KnowledgeBase[]>([])
const departments = ref<Department[]>([])
const dialog = ref(false)
const creating = ref(false)

const isAdmin = computed(() => authStore.isAdmin)
// super_admin 可选全部部门;dept_admin 只能选本部门
const deptOptions = computed(() => {
  if (authStore.isSuperAdmin) return departments.value
  return departments.value.filter((d) => d.id === authStore.departmentId)
})

const form = reactive({
  name: '',
  description: '',
  department_id: null as number | null,
  retrieval_type: 'hybrid',
  chunk_size: 500,
  chunk_overlap: 50,
  parent_chunk_size: 2000,
})

function deptName(id: number): string {
  return departments.value.find((d) => d.id === id)?.name || `部门#${id}`
}

onMounted(async () => {
  departments.value = await listDepartments()
  await load()
})

async function load() {
  kbs.value = await listKnowledgeBases()
}

function openCreate() {
  form.name = ''
  form.description = ''
  form.department_id = authStore.isSuperAdmin ? null : authStore.departmentId
  form.retrieval_type = 'hybrid'
  form.chunk_size = 500
  form.chunk_overlap = 50
  form.parent_chunk_size = 2000
  dialog.value = true
}

async function create() {
  if (!form.name.trim()) {
    ElMessage.warning('请输入知识库名称')
    return
  }
  if (form.department_id === null) {
    ElMessage.warning('请选择所属部门')
    return
  }
  creating.value = true
  try {
    await createKnowledgeBase({ ...form, department_id: form.department_id } as any)
    ElMessage.success('创建成功')
    dialog.value = false
    await load()
  } finally {
    creating.value = false
  }
}

function goDetail(id: number) {
  router.push(`/knowledge/${id}`)
}

function remove(kb: KnowledgeBase) {
  ElMessageBox.confirm(`确定删除知识库「${kb.name}」吗?其中的文档与向量数据都会被删除。`, '提示', {
    type: 'warning',
  }).then(async () => {
    await deleteKnowledgeBase(kb.id)
    ElMessage.success('已删除')
    await load()
  })
}
</script>

<style scoped>
.kb-page {
  padding: 4px;
}
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.toolbar h2 {
  font-size: 20px;
}
.sub {
  color: #9aa3b2;
  font-size: 13px;
  margin-top: 4px;
}
.kb-card {
  border-radius: 14px;
  cursor: pointer;
  margin-bottom: 16px;
}
.kb-head {
  display: flex;
  gap: 12px;
  align-items: center;
}
.kb-icon {
  font-size: 30px;
}
.kb-name {
  font-size: 16px;
  font-weight: 600;
}
.kb-time {
  font-size: 12px;
  color: #b3bac7;
  margin-top: 2px;
}
.kb-desc {
  color: #6b7280;
  font-size: 13px;
  margin: 14px 0;
  min-height: 36px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.kb-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.doc-count {
  color: #9aa3b2;
  font-size: 13px;
}
.kb-actions {
  margin-top: 14px;
  text-align: right;
  border-top: 1px solid #f0f2f6;
  padding-top: 10px;
}
.form-tip {
  font-size: 12px;
  color: #9aa3b2;
  line-height: 1.5;
  margin: -4px 0 12px 90px;
}
</style>
