import http from './index'
import type { ChunkItem, Department, DocumentItem, DocumentVersion, KnowledgeBase } from '@/types'

export function listDepartments(): Promise<Department[]> {
  return http.get('/departments').then((r) => r.data)
}

export function listKnowledgeBases(): Promise<KnowledgeBase[]> {
  return http.get('/knowledge-bases').then((r) => r.data)
}

export function createKnowledgeBase(data: {
  name: string
  description?: string
  department_id: number
  is_public?: boolean
  retrieval_type: string
  chunk_size: number
  chunk_overlap: number
  parent_chunk_size?: number
}): Promise<KnowledgeBase> {
  return http.post('/knowledge-bases', data).then((r) => r.data)
}

export function deleteKnowledgeBase(id: number) {
  return http.delete(`/knowledge-bases/${id}`)
}

export function listDocuments(kbId: number): Promise<DocumentItem[]> {
  return http.get(`/knowledge-bases/${kbId}/documents`).then((r) => r.data)
}

export function uploadDocument(
  kbId: number,
  file: File,
  chunkSize?: number,
  chunkOverlap?: number,
): Promise<DocumentItem> {
  const form = new FormData()
  form.append('file', file)
  if (chunkSize) form.append('chunk_size', String(chunkSize))
  if (chunkOverlap !== undefined) form.append('chunk_overlap', String(chunkOverlap))
  return http
    .post(`/knowledge-bases/${kbId}/documents`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    .then((r) => r.data)
}

export function deleteDocument(kbId: number, documentId: number) {
  return http.delete(`/knowledge-bases/${kbId}/documents/${documentId}`)
}

export interface ParseProgress {
  progress: number
  status: 'pending' | 'parsing' | 'completed' | 'failed'
}

export function getDocumentProgress(kbId: number, documentId: number): Promise<ParseProgress> {
  return http
    .get(`/knowledge-bases/${kbId}/documents/${documentId}/progress`)
    .then((r) => r.data)
}

export function listChunks(kbId: number, documentId: number): Promise<ChunkItem[]> {
  return http.get(`/knowledge-bases/${kbId}/documents/${documentId}/chunks`).then((r) => r.data)
}

export function listDocumentVersions(kbId: number, documentId: number): Promise<DocumentVersion[]> {
  return http.get(`/knowledge-bases/${kbId}/documents/${documentId}/versions`).then((r) => r.data)
}

export function getVersionChunks(kbId: number, documentId: number, version: number): Promise<ChunkItem[]> {
  return http.get(`/knowledge-bases/${kbId}/documents/${documentId}/versions/${version}/chunks`).then((r) => r.data)
}

export function rollbackDocument(kbId: number, documentId: number): Promise<DocumentItem> {
  return http.post(`/knowledge-bases/${kbId}/documents/${documentId}/rollback`).then((r) => r.data)
}

export function updateChunk(chunkId: number, content: string): Promise<ChunkItem> {
  return http.put(`/chunks/${chunkId}`, { content }).then((r) => r.data)
}

export function deleteChunk(chunkId: number) {
  return http.delete(`/chunks/${chunkId}`)
}
