// 全局类型定义

export interface KnowledgeBase {
  id: number
  name: string
  description: string | null
  retrieval_type: string
  chunk_size: number
  chunk_overlap: number
  doc_count: number
  created_at: string
}

export interface DocumentItem {
  id: number
  kb_id: number
  filename: string
  file_type: string
  status: string
  error_msg: string | null
  chunk_count: number
  created_at: string
}

export interface ChunkItem {
  id: number
  kb_id: number
  document_id: number
  content: string
  chunk_index: number
  created_at: string
}

export interface ChatSession {
  id: number
  name: string
  created_at: string
}

export interface ChatMessage {
  id: number
  session_id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string
}
