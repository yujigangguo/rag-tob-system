<template>
  <div class="detail-page fade-enter">
    <div class="toolbar">
      <div class="left">
        <el-button text :icon="ArrowLeft" @click="$router.push('/knowledge')">返回</el-button>
        <h2>{{ kb?.name || '知识库详情' }}</h2>
        <el-tag size="small" :type="kb?.retrieval_type === 'hybrid' ? 'primary' : 'info'">
          {{ kb?.retrieval_type === 'hybrid' ? '混合检索' : '稠密检索' }}
        </el-tag>
      </div>
      <el-button v-if="isAdmin" type="primary" class="gradient-btn" :icon="Upload" @click="uploadDialog = true">
        上传文档
      </el-button>
    </div>

    <div class="content">
      <!-- 文档列表 -->
      <div class="doc-list">
        <div class="panel-title">文档列表({{ docs.length }})</div>
        <el-empty v-if="docs.length === 0" description="暂无文档,点击右上角上传" />
        <div
          v-for="doc in docs"
          :key="doc.id"
          class="doc-item"
          :class="{ active: doc.id === currentDocId }"
          @click="openDoc(doc)"
        >
          <div class="doc-name">📄 {{ doc.filename }}</div>
          <div class="doc-meta">
            <el-tag size="small" :type="statusType(doc.status)">{{ statusText(doc.status) }}</el-tag>
            <span>块 {{ doc.chunk_count }}</span>
          </div>
          <el-icon v-if="isAdmin" class="doc-del" @click.stop="removeDoc(doc)"><Delete /></el-icon>
        </div>
      </div>

      <!-- 文档块预览 -->
      <div class="chunk-list">
        <div class="panel-title">文档块预览</div>
        <el-empty v-if="!currentDoc" description="点击左侧文档查看其内容块" />
        <template v-else>
          <div v-for="chunk in chunks" :key="chunk.id" :id="'chunk-' + chunk.id" class="chunk-item"
               :class="{ 'chunk-highlight': chunk.id === highlightedChunkId }">
            <div class="chunk-index">#{{ chunk.chunk_index + 1 }}</div>
            <div class="chunk-content">{{ chunk.content }}</div>
            <div class="chunk-actions">
              <el-button v-if="isAdmin" text size="small" type="primary" @click="editChunk(chunk)">编辑</el-button>
              <el-button v-if="isAdmin" text size="small" type="danger" @click="removeChunk(chunk)">删除</el-button>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- 上传文档弹窗 -->
    <el-dialog v-model="uploadDialog" title="上传文档" width="500px">
      <el-upload
        drag
        :auto-upload="false"
        :limit="1"
        :on-change="onFileChange"
        :on-remove="() => (selectedFile = null)"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">拖拽文件到此处,或<em>点击选择</em></div>
        <template #tip>
          <div class="el-upload__tip">支持 PDF、PPT、Markdown、TXT、图片(图片暂不解析内容);单个文件最大 10MB</div>
        </template>
      </el-upload>

      <el-form label-width="90px" style="margin-top: 16px">
        <el-form-item label="切块大小">
          <el-input-number v-model="parseForm.chunk_size" :min="50" :max="4000" :step="50" />
        </el-form-item>
        <el-form-item label="重叠大小">
          <el-input-number v-model="parseForm.chunk_overlap" :min="0" :max="1000" :step="10" />
        </el-form-item>
      </el-form>

      <!-- 解析进度条 -->
      <div v-if="uploading" class="parse-progress">
        <el-progress
          :percentage="parseProgress"
          :status="parseProgress >= 100 ? 'success' : undefined"
          :stroke-width="8"
        />
        <div class="parse-status">{{ parseStatus }}</div>
      </div>

      <template #footer>
        <el-button @click="uploadDialog = false">取消</el-button>
        <el-button type="primary" class="gradient-btn" :loading="uploading" @click="doUpload">
          上传并解析
        </el-button>
      </template>
    </el-dialog>

    <!-- 编辑文档块弹窗 -->
    <el-dialog v-model="editDialog" title="编辑文档块" width="640px">
      <el-input v-model="editContent" type="textarea" :rows="10" />
      <template #footer>
        <el-button @click="editDialog = false">取消</el-button>
        <el-button type="primary" class="gradient-btn" :loading="saving" @click="saveChunk">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Upload, UploadFilled, Delete } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import {
  deleteChunk,
  deleteDocument,
  getDocumentProgress,
  listChunks,
  listDocuments,
  listKnowledgeBases,
  updateChunk,
  uploadDocument,
} from '@/api/knowledgeBase'
import type { ChunkItem, DocumentItem, KnowledgeBase } from '@/types'

const route = useRoute()
const kbId = Number(route.params.id)
const authStore = useAuthStore()
const isAdmin = authStore.isAdmin

const kb = ref<KnowledgeBase | null>(null)
const docs = ref<DocumentItem[]>([])
const chunks = ref<ChunkItem[]>([])
const currentDocId = ref<number | null>(null)
const currentDoc = ref<DocumentItem | null>(null)

const uploadDialog = ref(false)
const uploading = ref(false)
const selectedFile = ref<File | null>(null)
const parseForm = reactive({ chunk_size: 500, chunk_overlap: 50 })
const parseProgress = ref(0)
const parseStatus = ref('')

const editDialog = ref(false)
const saving = ref(false)
const editingChunk = ref<ChunkItem | null>(null)
const editContent = ref('')
const highlightedChunkId = ref<number | null>(null)

onMounted(async () => {
  const kbs = await listKnowledgeBases()
  kb.value = kbs.find((k) => k.id === kbId) || null
  await loadDocs()
  // 深链:从对话引用点击跳转而来,自动打开对应文档并定位到块
  const targetDocId = Number(route.query.doc) || null
  if (targetDocId) {
    const doc = docs.value.find((d) => d.id === targetDocId)
    if (doc) {
      await openDoc(doc)
      const targetChunkId = Number(route.query.chunk) || null
      if (targetChunkId) {
        highlightedChunkId.value = targetChunkId
        nextTick(() => {
          const el = document.getElementById('chunk-' + targetChunkId)
          el?.scrollIntoView({ behavior: 'smooth', block: 'center' })
        })
      }
    }
  }
})

async function loadDocs() {
  docs.value = await listDocuments(kbId)
}

function onFileChange(uploadFile: any) {
  selectedFile.value = uploadFile.raw
}

function statusText(s: string) {
  return { pending: '待解析', parsing: '解析中', completed: '已完成', failed: '失败' }[s] || s
}

function statusType(s: string) {
  return { pending: 'info', parsing: 'warning', completed: 'success', failed: 'danger' }[s] || 'info'
}

async function doUpload() {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }
  uploading.value = true
  parseProgress.value = 0
  parseStatus.value = '正在上传...'

  try {
    // 上传(接口立即返回,后端后台异步解析)
    const doc = await uploadDocument(
      kbId, selectedFile.value, parseForm.chunk_size, parseForm.chunk_overlap,
    )
    parseStatus.value = '正在解析文档...'
    // 轮询真实解析进度
    await pollProgress(doc.id)

    parseProgress.value = 100
    parseStatus.value = '解析完成'
    ElMessage.success('上传解析成功')
    window.setTimeout(() => {
      uploadDialog.value = false
      selectedFile.value = null
      parseProgress.value = 0
      parseStatus.value = ''
      loadDocs()
    }, 500)
  } catch {
    parseStatus.value = '解析失败,请重试'
  } finally {
    uploading.value = false
  }
}

async function pollProgress(documentId: number) {
  while (true) {
    const p = await getDocumentProgress(kbId, documentId)
    parseProgress.value = p.progress
    if (p.status === 'completed') {
      parseProgress.value = 100
      return
    }
    if (p.status === 'failed') {
      throw new Error('解析失败')
    }
    await new Promise((r) => setTimeout(r, 800))
  }
}

async function openDoc(doc: DocumentItem) {
  currentDocId.value = doc.id
  currentDoc.value = doc
  chunks.value = await listChunks(kbId, doc.id)
}

async function removeDoc(doc: DocumentItem) {
  await ElMessageBox.confirm(`确定删除文档「${doc.filename}」吗?`, '提示', { type: 'warning' })
  await deleteDocument(kbId, doc.id)
  ElMessage.success('已删除')
  if (currentDocId.value === doc.id) {
    currentDocId.value = null
    currentDoc.value = null
    chunks.value = []
  }
  await loadDocs()
}

function editChunk(chunk: ChunkItem) {
  editingChunk.value = chunk
  editContent.value = chunk.content
  editDialog.value = true
}

async function saveChunk() {
  if (!editingChunk.value) return
  saving.value = true
  try {
    await updateChunk(editingChunk.value.id, editContent.value)
    ElMessage.success('已保存(向量已更新)')
    editDialog.value = false
    if (currentDoc.value) {
      chunks.value = await listChunks(kbId, currentDoc.value.id)
    }
  } finally {
    saving.value = false
  }
}

async function removeChunk(chunk: ChunkItem) {
  await ElMessageBox.confirm('确定删除该文档块吗?', '提示', { type: 'warning' })
  await deleteChunk(chunk.id)
  ElMessage.success('已删除')
  if (currentDoc.value) {
    chunks.value = await listChunks(kbId, currentDoc.value.id)
  }
}
</script>

<style scoped>
.detail-page {
  padding: 4px;
}
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.left h2 {
  font-size: 20px;
}
.content {
  display: flex;
  gap: 16px;
  height: calc(100vh - 180px);
}
.doc-list {
  width: 300px;
  background: #fff;
  border-radius: 14px;
  padding: 16px;
  overflow: auto;
}
.chunk-list {
  flex: 1;
  background: #fff;
  border-radius: 14px;
  padding: 16px;
  overflow: auto;
}
.panel-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #3a4050;
}
.doc-item {
  position: relative;
  padding: 12px;
  border-radius: 10px;
  cursor: pointer;
  margin-bottom: 8px;
  border: 1px solid transparent;
}
.doc-item:hover {
  background: #f6f8fd;
}
.doc-item.active {
  background: #eef1ff;
  border-color: #4f6ef7;
}
.doc-name {
  font-size: 14px;
  font-weight: 500;
  padding-right: 20px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.doc-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
  color: #9aa3b2;
  font-size: 12px;
}
.doc-del {
  position: absolute;
  top: 12px;
  right: 12px;
  color: #c0c6d2;
}
.doc-del:hover {
  color: #f56c6c;
}
.chunk-item {
  border: 1px solid #eef0f4;
  border-radius: 12px;
  padding: 14px;
  margin-bottom: 12px;
}
.chunk-item.chunk-highlight {
  border-color: #4f6ef7;
  background: #eef1ff;
  box-shadow: 0 0 0 2px rgba(79, 110, 247, 0.15);
}
.chunk-index {
  color: #4f6ef7;
  font-weight: 600;
  font-size: 13px;
  margin-bottom: 8px;
}
.chunk-content {
  white-space: pre-wrap;
  line-height: 1.7;
  font-size: 14px;
  color: #3a4050;
}
.chunk-actions {
  text-align: right;
  margin-top: 8px;
}
.parse-progress {
  margin-top: 8px;
}
.parse-status {
  margin-top: 6px;
  font-size: 13px;
  color: #6b7280;
  text-align: center;
}
</style>
