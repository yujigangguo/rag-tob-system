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
                <el-dropdown-item command="delete">删除</el-dropdown-item>
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
          <p>开始你的第一次提问吧</p>
        </div>
        <div v-for="(m, i) in messages" :key="i" class="msg" :class="m.role">
          <div class="bubble">{{ m.content }}</div>
        </div>
        <div v-if="streaming" class="msg assistant">
          <div class="bubble typing"><span class="cursor"></span></div>
        </div>
      </div>
      <div class="input-area">
        <el-input
          v-model="question"
          type="textarea"
          :rows="3"
          placeholder="输入你的问题,Enter 发送,Shift+Enter 换行"
          @keydown.enter.exact.prevent="send"
        />
        <div class="input-actions">
          <span class="hint">已选 {{ selectedKbIds.length }} 个知识库</span>
          <el-button type="primary" class="gradient-btn" :loading="streaming" :icon="Promotion" @click="send">
            发送
          </el-button>
        </div>
      </div>
    </div>

    <!-- 右侧参数面板 -->
    <div class="param-panel">
      <div class="param-title">参数设置</div>

      <div class="param-block">
        <label>知识库(可多选)</label>
        <el-select v-model="selectedKbIds" multiple placeholder="选择知识库" style="width: 100%">
          <el-option v-for="kb in kbs" :key="kb.id" :label="kb.name" :value="kb.id" />
        </el-select>
      </div>

      <div class="param-block">
        <label>大模型</label>
        <el-select v-model="params.model" style="width: 100%">
          <el-option label="qwen-max" value="qwen-max" />
          <el-option label="qwen-plus" value="qwen-plus" />
          <el-option label="qwen-turbo" value="qwen-turbo" />
        </el-select>
      </div>

      <div class="param-block">
        <label>温度 temperature:{{ params.temperature.toFixed(2) }}</label>
        <el-slider v-model="params.temperature" :min="0" :max="2" :step="0.05" />
      </div>

      <div class="param-block">
        <label>Top P:{{ params.top_p.toFixed(2) }}</label>
        <el-slider v-model="params.top_p" :min="0" :max="1" :step="0.05" />
      </div>

      <div class="param-block">
        <label>最长输出 token 数</label>
        <el-input-number v-model="params.max_tokens" :min="64" :max="8192" :step="256" style="width: 100%" />
      </div>

      <div class="param-block">
        <label>历史对话轮数</label>
        <el-input-number v-model="params.history_rounds" :min="0" :max="20" style="width: 100%" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Promotion, ChatLineRound, MoreFilled } from '@element-plus/icons-vue'
import { listKnowledgeBases } from '@/api/knowledgeBase'
import {
  createSession,
  deleteSession,
  listMessages,
  listSessions,
  renameSession,
  streamChat,
} from '@/api/chat'
import type { ChatMessage, ChatSession, KnowledgeBase } from '@/types'

const sessions = ref<ChatSession[]>([])
const currentSessionId = ref<number | null>(null)
const messages = ref<ChatMessage[]>([])
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
})

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

async function send() {
  const q = question.value.trim()
  if (!q) return
  if (selectedKbIds.value.length === 0) {
    ElMessage.warning('请先选择至少一个知识库')
    return
  }
  question.value = ''
  messages.value.push({ id: 0, session_id: 0, role: 'user', content: q, created_at: '' })
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
.session-panel {
  width: 220px;
  background: #fff;
  border-radius: 14px;
  padding: 14px;
  display: flex;
  flex-direction: column;
}
.new-session {
  width: 100%;
}
.session-list {
  margin-top: 12px;
  overflow: auto;
  flex: 1;
}
.session-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  color: #3a4050;
  font-size: 14px;
}
.session-item:hover {
  background: #f2f4fb;
}
.session-item.active {
  background: linear-gradient(135deg, #eef1ff, #f3efff);
  color: #4f6ef7;
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
}
.session-item:hover .more {
  opacity: 1;
}
.chat-main {
  flex: 1;
  background: #fff;
  border-radius: 14px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
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
  color: #b3bac7;
}
.empty-icon {
  font-size: 48px;
}
.msg {
  display: flex;
  margin-bottom: 16px;
}
.msg.user {
  justify-content: flex-end;
}
.bubble {
  max-width: 72%;
  padding: 12px 16px;
  border-radius: 14px;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
  font-size: 14px;
}
.msg.user .bubble {
  background: linear-gradient(135deg, #4f6ef7, #7b5cf0);
  color: #fff;
  border-bottom-right-radius: 4px;
}
.msg.assistant .bubble {
  background: #f2f4fb;
  color: #1f2329;
  border-bottom-left-radius: 4px;
}
.cursor {
  display: inline-block;
  width: 8px;
  height: 16px;
  background: #4f6ef7;
  animation: blink 0.8s infinite;
  vertical-align: middle;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
.input-area {
  border-top: 1px solid #eef0f4;
  padding: 14px 18px;
}
.input-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 10px;
}
.hint {
  color: #9aa3b2;
  font-size: 12px;
}
.param-panel {
  width: 260px;
  background: #fff;
  border-radius: 14px;
  padding: 18px;
  overflow: auto;
}
.param-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 16px;
}
.param-block {
  margin-bottom: 16px;
}
.param-block label {
  display: block;
  font-size: 13px;
  color: #5a6272;
  margin-bottom: 8px;
}
</style>
