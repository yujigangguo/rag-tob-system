import http from './index'
import type { ChatMessage, ChatSession, Citation } from '@/types'

export type { Citation }

export function listSessions(): Promise<ChatSession[]> {
  return http.get('/chat/sessions').then((r) => r.data)
}

export function createSession(name: string): Promise<ChatSession> {
  return http.post('/chat/sessions', { name }).then((r) => r.data)
}

export function renameSession(id: number, name: string): Promise<ChatSession> {
  return http.put(`/chat/sessions/${id}`, { name }).then((r) => r.data)
}

export function deleteSession(id: number) {
  return http.delete(`/chat/sessions/${id}`)
}

export function listMessages(sessionId: number): Promise<ChatMessage[]> {
  return http.get(`/chat/sessions/${sessionId}/messages`).then((r) => r.data)
}

export interface ChatParams {
  session_id?: number | null
  session_name?: string | null
  question: string
  kb_ids: number[]
  model: string
  temperature: number
  top_p: number
  max_tokens: number
  history_rounds: number
}

// 流式问答:通过 fetch 读取 SSE,onToken 回调逐字返回,onCitations 回调接收引用映射
export async function streamChat(
  params: ChatParams,
  onToken: (token: string) => void,
  onCitations?: (citations: Citation[]) => void,
): Promise<string> {
  const token = localStorage.getItem('token')
  const resp = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(params),
  })

  if (!resp.ok || !resp.body) {
    throw new Error(`请求失败: ${resp.status}`)
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let full = ''
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    // SSE 以 \n\n 分隔
    const chunks = buffer.split('\n\n')
    buffer = chunks.pop() || ''
    for (const chunk of chunks) {
      const line = chunk.trim()
      if (!line.startsWith('data:')) continue
      const payload = line.slice(5).trim()
      if (payload === '[DONE]') continue
      try {
        const obj = JSON.parse(payload)
        if (obj.token) {
          full += obj.token
          onToken(obj.token)
        } else if (obj.citations && onCitations) {
          onCitations(obj.citations)
        }
      } catch {
        /* 忽略解析失败的块 */
      }
    }
  }
  return full
}
