<template>
  <div class="chat-page">
    <!-- 左侧会话列表 -->
    <div class="session-panel">
      <el-button type="primary" class="new-session gradient-btn" :icon="Plus" @click="newSession">
        新建对话
      </el-button>
      <div class="session-list">
        <div
          v-for="s in sessions"
          :key="s.id"
          class="session-item"
          :class="{ active: s.id === currentSessionId }"
          @click="selectSession(s.id)"
        >
          <el-icon><ChatLineRound /></el-icon>
          <span class="session-name">{{ s.name }}</span>
          <el-dropdown trigger="click" @command="(cmd: string) => onSessionCmd(cmd, s)">
            <el-icon class="more" @click.stop><MoreFilled /></el-icon>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="rename">重命名</el-dropdown-item>
                <el-dropdown-item command="export_md">导出 Markdown</el-dropdown-item>
                <el-dropdown-item command="export_json">导出 JSON</el-dropdown-item>
                <el-dropdown-item divided command="delete">删除</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </div>

    <!-- 中间对话区 -->
    <div class="chat-main">
      <div class="message-area" ref="messageArea">
        <div v-if="messages.length === 0" class="empty">
          <div class="empty-icon">💬</div>
          <h3>开始你的第一次提问吧</h3>
          <p>选择知识库，输入问题即可获得智能回答</p>
          <div class="shortcuts">
            <div class="shortcut-item">
              <kbd>Enter</kbd>
              <span>发送消息</span>
            </div>
            <div class="shortcut-item">
              <kbd>Shift + Enter</kbd>
              <span>换行</span>
            </div>
          </div>
        </div>
        <div v-for="(m, i) in messages" :key="i" class="msg" :class="m.role">
          <template v-if="m.role === 'user'">
            <div class="bubble-wrapper">
              <div class="bubble">{{ m.content }}</div>
              <div class="msg-time">{{ formatTime(m.created_at) }}</div>
            </div>
          </template>
          <template v-else>
            <div class="assistant-block">
              <div class="bubble">
                <template v-for="(seg, si) in renderSegments(m)" :key="si">
                  <span v-if="seg.type === 'text'" class="seg-text">{{ seg.text }}</span>
                  <a
                    v-else
                    class="cite-link"
                    href="javascript:;"
                    :title="seg.citation ? '查看引用来源' : undefined"
                    @click.prevent="seg.citation && goCitation(seg.citation)"
                  >[{{ seg.text }}]</a>
                </template>
              </div>
              <div class="msg-footer">
                <div v-if="m.kb_ids && m.kb_ids.length" class="msg-source">
                  <el-icon><Search /></el-icon>
                  <span>检索: {{ kbNames(m.kb_ids) }}</span>
                </div>
                <div class="msg-time">{{ formatTime(m.created_at) }}</div>
              </div>
            </div>
          </template>
        </div>
        <div v-if="streaming" class="msg assistant">
          <div class="assistant-block">
            <div class="bubble typing">
              <span class="cursor"></span>
              <span class="typing-text">正在思考...</span>
            </div>
          </div>
        </div>
      </div>
      <div class="input-area">
        <div class="input-wrapper">
          <el-input
            v-model="question"
            type="textarea"
            :rows="3"
            placeholder="输入你的问题..."
            @keydown.enter.exact.prevent="send"
            @keydown.shift.enter="newline"
          />
          <div class="input-actions">
            <div class="input-hints">
              <span class="hint">
                <el-icon><InfoFilled /></el-icon>
                已选 {{ selectedKbIds.length }} 个知识库
              </span>
              <span class="shortcut-hint">
                <kbd>Enter</kbd> 发送 · <kbd>Shift+Enter</kbd> 换行
              </span>
            </div>
            <el-button 
              type="primary" 
              class="gradient-btn send-btn" 
              :loading="streaming" 
              :icon="Promotion" 
              @click="send"
              :disabled="!question.trim() || selectedKbIds.length === 0"
            >
              发送
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧参数面板 -->
    <div class="param-panel">
      <div class="param-title">
        <el-icon><Setting /></el-icon>
        <span>参数设置</span>
      </div>

      <div class="param-block">
        <label>
          <el-icon><FolderOpened /></el-icon>
          知识库 (可多选)
        </label>
        <el-select 
          v-model="selectedKbIds" 
          multiple 
          placeholder="选择知识库" 
          style="width: 100%"
          collapse-tags
          collapse-tags-tooltip
        >
          <el-option v-for="kb in kbs" :key="kb.id" :label="kb.name" :value="kb.id" />
        </el-select>
      </div>

      <div class="param-block">
        <label>
          <el-icon><Cpu /></el-icon>
          大模型
        </label>
        <el-select v-model="params.model" style="width: 100%">
          <el-option label="qwen-max" value="qwen-max" />
          <el-option label="qwen-plus" value="qwen-plus" />
          <el-option label="qwen-turbo" value="qwen-turbo" />
        </el-select>
      </div>

      <div class="param-block">
        <label>
          <el-icon><Operation /></el-icon>
          温度: {{ params.temperature.toFixed(2) }}
        </label>
        <el-slider v-model="params.temperature" :min="0" :max="2" :step="0.05" :show-tooltip="false" />
        <div class="slider-marks">
          <span>精确</span>
          <span>平衡</span>
          <span>创意</span>
        </div>
      </div>

      <div class="param-block">
        <label>
          <el-icon><Filter /></el-icon>
          Top P: {{ params.top_p.toFixed(2) }}
        </label>
        <el-slider v-model="params.top_p" :min="0" :max="1" :step="0.05" :show-tooltip="false" />
      </div>

      <div class="param-block">
        <label>
          <el-icon><Document /></el-icon>
          最长输出 token 数
        </label>
        <el-input-number v-model="params.max_tokens" :min="64" :max="8192" :step="256" style="width: 100%" />
      </div>

      <div class="param-block">
        <label>
          <el-icon><ChatDotRound /></el-icon>
          历史对话轮数
        </label>
        <el-input-number v-model="params.history_rounds" :min="0" :max="20" style="width: 100%" />
      </div>

      <div class="param-tips">
        <el-divider />
        <h4>💡 使用提示</h4>
        <ul>
          <li>选择相关知识库可获得更精准的回答</li>
          <li>温度越低，回答越精确；越高越有创意</li>
          <li>点击引用 <span class="cite-example">[1]</span> 可查看原文</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Plus, 
  Promotion, 
  ChatLineRound, 
  MoreFilled,
  Search,
  InfoFilled,
  Setting,
  FolderOpened,
  Cpu,
  Operation,
  Filter,
  Document,
  ChatDotRound
} from '@element-plus/icons-vue'
import { listKnowledgeBases } from '@/api/knowledgeBase'
import {
  createSession,
  deleteSession,
  exportSession,
  listMessages,
  listSessions,
  renameSession,
  streamChat,
  type Citation,
} from '@/api/chat'
import type { ChatMessage, ChatSession, KnowledgeBase } from '@/types'

interface Msg extends ChatMessage {
  citations?: Citation[]
}

const LAST_KB_KEY = 'chat_last_kb_ids'  // localStorage:记住上次勾选的知识库

interface Seg {
  type: 'text' | 'cite'
  text: string
  citation?: Citation
}

const router = useRouter()
const sessions = ref<ChatSession[]>([])
const currentSessionId = ref<number | null>(null)
const messages = ref<Msg[]>([])
const kbs = ref<KnowledgeBase[]>([])
const selectedKbIds = ref<number[]>([])
const question = ref('')
const streaming = ref(false)
const messageArea = ref<HTMLElement>()

const params = reactive({
  model: 'qwen-max',
  temperature: 0.7,
  top_p: 0.8,
  max_tokens: 2048,
  history_rounds: 5,
})

onMounted(async () => {
  await Promise.all([loadSessions(), loadKbs()])
  restoreLastKbs()
})

// 进入页面时恢复上次勾选的知识库(与当前可见库求交集,防止权限变化后勾了不可见的库)
function restoreLastKbs() {
  try {
    const raw = localStorage.getItem(LAST_KB_KEY)
    if (!raw) return
    const ids = JSON.parse(raw) as number[]
    const valid = new Set(kbs.value.map((k) => k.id))
    selectedKbIds.value = ids.filter((id) => valid.has(id))
  } catch {
    /* 忽略损坏的本地数据 */
  }
}

// 勾选变化时保存
watch(selectedKbIds, (ids) => {
  localStorage.setItem(LAST_KB_KEY, JSON.stringify(ids))
})

function kbNames(ids: number[]): string {
  return ids
    .map((id) => kbs.value.find((k) => k.id === id)?.name || `知识库#${id}`)
    .join(' · ')
}

async function loadKbs() {
  kbs.value = await listKnowledgeBases()
}

async function loadSessions() {
  sessions.value = await listSessions()
}

async function selectSession(id: number) {
  currentSessionId.value = id
  messages.value = await listMessages(id)
  scrollBottom()
}

async function newSession() {
  const s = await createSession('新对话')
  sessions.value.unshift(s)
  currentSessionId.value = s.id
  messages.value = []
}

function onSessionCmd(cmd: string, s: ChatSession) {
  if (cmd === 'rename') {
    ElMessageBox.prompt('输入新的会话名称', '重命名', {
      inputValue: s.name,
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    }).then(async ({ value }) => {
      await renameSession(s.id, value)
      await loadSessions()
    })
  } else if (cmd === 'export_md') {
    handleExport(s.id, 'markdown')
  } else if (cmd === 'export_json') {
    handleExport(s.id, 'json')
  } else if (cmd === 'delete') {
    ElMessageBox.confirm('确定删除该会话吗?', '提示', { type: 'warning' }).then(async () => {
      await deleteSession(s.id)
      if (currentSessionId.value === s.id) {
        currentSessionId.value = null
        messages.value = []
      }
      await loadSessions()
    })
  }
}

async function handleExport(sessionId: number, format: 'markdown' | 'json') {
  try {
    await exportSession(sessionId, format)
    ElMessage.success('导出成功')
  } catch (error: any) {
    ElMessage.error(error.message || '导出失败')
  }
}

async function send() {
  const q = question.value.trim()
  if (!q) return
  if (selectedKbIds.value.length === 0) {
    ElMessage.warning('请先选择至少一个知识库')
    return
  }
  question.value = ''
  messages.value.push({ id: 0, session_id: 0, role: 'user', content: q, created_at: new Date().toISOString() })
  messages.value.push({ id: 0, session_id: 0, role: 'assistant', content: '', created_at: '' })
  streaming.value = true
  scrollBottom()

  const assistantMsg = messages.value[messages.value.length - 1]
  try {
    await streamChat(
      {
        session_id: currentSessionId.value,
        question: q,
        kb_ids: selectedKbIds.value,
        ...params,
      },
      (token) => {
        assistantMsg.content += token
        scrollBottom()
      },
      (citations) => {
        assistantMsg.citations = citations
      },
    )
    // 若新建了会话,刷新会话列表拿到真实 session_id
    if (currentSessionId.value === null) {
      await loadSessions()
    }
  } catch (e: any) {
    assistantMsg.content = '⚠️ ' + (e.message || '生成失败,请重试')
  } finally {
    streaming.value = false
  }
}

// 换行
function newline() {
  question.value += '\n'
}

// 格式化时间
function formatTime(dateStr: string): string {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  // 今天内只显示时间
  if (diff < 86400000 && date.getDate() === now.getDate()) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  
  // 今年内显示月日时间
  if (date.getFullYear() === now.getFullYear()) {
    return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' }) + ' ' + 
           date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  
  // 其他显示完整日期
  return date.toLocaleDateString('zh-CN')
}

// 把回答拆成普通文本段 + 可点击引用段([N])
function renderSegments(m: Msg): Seg[] {
  const segs: Seg[] = []
  const regex = /\[(\d+)\]/g
  let last = 0
  let match: RegExpExecArray | null
  while ((match = regex.exec(m.content)) !== null) {
    if (match.index > last) {
      segs.push({ type: 'text', text: m.content.slice(last, match.index) })
    }
    const idx = Number(match[1])
    const citation = m.citations?.find((c) => c.index === idx)
    segs.push({ type: 'cite', text: match[1], citation })
    last = match.index + match[0].length
  }
  if (last < m.content.length) {
    segs.push({ type: 'text', text: m.content.slice(last) })
  }
  return segs.length ? segs : [{ type: 'text', text: m.content }]
}

// 点击引用:跳转到知识库详情并定位到对应文档块
function goCitation(c: Citation) {
  const q = `doc=${c.document_id}${c.chunk_id ? `&chunk=${c.chunk_id}` : ''}`
  router.push(`/knowledge/${c.kb_id}?${q}`)
}

function scrollBottom() {
  nextTick(() => {
    if (messageArea.value) {
      messageArea.value.scrollTop = messageArea.value.scrollHeight
    }
  })
}
</script>

<style scoped>
.chat-page {
  display: flex;
  height: calc(100vh - 100px);
  gap: 16px;
}

/* 会话面板 */
.session-panel {
  width: 240px;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  padding: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-sm);
}

.new-session {
  width: 100%;
  height: 44px;
  font-size: 14px;
}

.session-list {
  margin-top: 16px;
  overflow: auto;
  flex: 1;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--text-secondary);
  font-size: 14px;
  transition: all var(--transition-fast);
}

.session-item:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.session-item.active {
  background: var(--brand-light);
  color: var(--brand);
  font-weight: 500;
}

.session-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.more {
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.session-item:hover .more {
  opacity: 1;
}

/* 聊天主区域 */
.chat-main {
  flex: 1;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.message-area {
  flex: 1;
  overflow: auto;
  padding: 24px;
}

.empty {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.empty h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.empty p {
  font-size: 14px;
  margin-bottom: 24px;
}

.shortcuts {
  display: flex;
  gap: 24px;
}

.shortcut-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.shortcut-item kbd {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-light);
  border-radius: 6px;
  padding: 2px 8px;
  font-family: inherit;
  font-size: 12px;
  color: var(--text-secondary);
}

/* 消息样式 */
.msg {
  display: flex;
  margin-bottom: 20px;
  animation: slideUp var(--transition-slow);
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.msg.user {
  justify-content: flex-end;
}

.bubble-wrapper {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.bubble {
  max-width: 70%;
  padding: 14px 18px;
  border-radius: var(--radius-lg);
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.7;
  font-size: 14px;
}

.msg.user .bubble {
  background: var(--brand-gradient);
  color: #fff;
  border-bottom-right-radius: var(--radius-sm);
}

.msg.assistant .bubble {
  background: var(--bg-tertiary);
  color: var(--text-primary);
  border-bottom-left-radius: var(--radius-sm);
}

.msg-time {
  font-size: 12px;
  color: var(--text-placeholder);
  margin-top: 6px;
  padding: 0 4px;
}

.assistant-block {
  max-width: 70%;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.assistant-block .bubble {
  max-width: 100%;
}

.msg-footer {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 8px;
}

.msg-source {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-tertiary);
}

.msg-source .el-icon {
  font-size: 14px;
}

.seg-text {
  white-space: pre-wrap;
}

.cite-link {
  color: var(--brand);
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  margin: 0 2px;
  padding: 1px 4px;
  background: var(--brand-light);
  border-radius: 4px;
  transition: all var(--transition-fast);
}

.cite-link:hover {
  background: var(--brand);
  color: #fff;
}

/* 打字动画 */
.typing {
  display: flex;
  align-items: center;
  gap: 8px;
}

.cursor {
  display: inline-block;
  width: 8px;
  height: 16px;
  background: var(--brand);
  animation: blink 0.8s infinite;
  border-radius: 2px;
}

.typing-text {
  font-size: 13px;
  color: var(--text-tertiary);
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* 输入区域 */
.input-area {
  border-top: 1px solid var(--border-lighter);
  padding: 16px 20px;
  background: var(--bg-primary);
}

.input-wrapper {
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  padding: 12px;
}

.input-wrapper :deep(.el-textarea__inner) {
  background: transparent;
  border: none;
  box-shadow: none !important;
  resize: none;
}

.input-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 12px;
}

.input-hints {
  display: flex;
  align-items: center;
  gap: 16px;
}

.hint {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--text-tertiary);
  font-size: 12px;
}

.shortcut-hint {
  font-size: 12px;
  color: var(--text-placeholder);
}

.shortcut-hint kbd {
  background: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: 4px;
  padding: 1px 6px;
  font-family: inherit;
  font-size: 11px;
}

.send-btn {
  height: 40px;
  padding: 0 24px;
  font-size: 14px;
}

/* 参数面板 */
.param-panel {
  width: 280px;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  padding: 20px;
  overflow: auto;
  box-shadow: var(--shadow-sm);
}

.param-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 20px;
  color: var(--text-primary);
}

.param-block {
  margin-bottom: 20px;
}

.param-block label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 10px;
  font-weight: 500;
}

.param-block label .el-icon {
  font-size: 16px;
}

.slider-marks {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--text-placeholder);
  margin-top: 4px;
}

.param-tips {
  margin-top: 16px;
}

.param-tips h4 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--text-primary);
}

.param-tips ul {
  list-style: none;
  padding: 0;
}

.param-tips li {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  padding-left: 16px;
  position: relative;
}

.param-tips li::before {
  content: '•';
  position: absolute;
  left: 0;
  color: var(--brand);
}

.cite-example {
  color: var(--brand);
  font-weight: 600;
  background: var(--brand-light);
  padding: 1px 4px;
  border-radius: 4px;
}

/* 响应式 */
@media (max-width: 1024px) {
  .chat-page {
    flex-direction: column;
    height: auto;
  }
  
  .session-panel {
    width: 100%;
    height: 200px;
  }
  
  .param-panel {
    width: 100%;
  }
}

@media (max-width: 768px) {
  .chat-page {
    gap: 12px;
  }
  
  .session-panel {
    height: 160px;
    padding: 12px;
  }
  
  .chat-main {
    height: calc(100vh - 400px);
  }
  
  .bubble {
    max-width: 85%;
  }
  
  .input-actions {
    flex-direction: column;
    gap: 12px;
  }
  
  .input-hints {
    width: 100%;
    justify-content: space-between;
  }
  
  .send-btn {
    width: 100%;
  }
}
</style>
