// 全局类型定义

export type Role = 'super_admin' | 'dept_admin' | 'employee'

export interface Department {
  id: number
  name: string
}

export interface LoginResult {
  access_token: string
  token_type: string
  username: string
  role: Role
  department_id: number | null
  department_name: string | null
}

export interface KnowledgeBase {
  id: number
  name: string
  description: string | null
  department_id: number
  is_public: boolean
  retrieval_type: string
  chunk_size: number
  chunk_overlap: number
  parent_chunk_size: number
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
  parent_id: number | null
  created_at: string
}

export interface ChatSession {
  id: number
  name: string
  created_at: string
}

export interface Citation {
  index: number
  kb_id: number
  document_id: number
  chunk_id: number | null
}

export interface ChatMessage {
  id: number
  session_id: number
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[] | null
  kb_ids?: number[] | null
  created_at: string
}
