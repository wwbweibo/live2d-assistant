export type KnowledgeFileStatus = 'processing' | 'completed' | 'failed'

export interface KnowledgeFile {
  id: string
  name: string
  type: string
  size: number
  uploadTime: number
  status: KnowledgeFileStatus
  content?: string
  url?: string
  error?: string
} 