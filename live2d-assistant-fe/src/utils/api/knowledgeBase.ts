import type { KnowledgeFile } from '../../types/knowledge'

export async function uploadKnowledgeFile(serverUrl: string, file: File): Promise<any> {
  const formData = new FormData()
  formData.append('file_name', file.name)
  formData.append('file_data', file)
  const res = await fetch(`${serverUrl}/api/rag/upload`, {
    method: 'POST',
    body: formData
  })
  if (!res.ok) throw new Error('上传失败')
  return res.json()
}

export async function listKnowledgeFiles(serverUrl: string): Promise<KnowledgeFile[]> {
  const res = await fetch(`${serverUrl}/api/rag/list`)
  if (!res.ok) throw new Error('获取文件列表失败')
  return res.json()
}

export async function deleteKnowledgeFile(serverUrl: string, fileId: string): Promise<void> {
  const res = await fetch(`${serverUrl}/api/rag/delete/${fileId}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('删除失败')
}

export async function getKnowledgeFileContent(serverUrl: string, fileId: string): Promise<KnowledgeFile> {
  const res = await fetch(`${serverUrl}/api/rag/content/${fileId}`)
  if (!res.ok) throw new Error('获取内容失败')
  return res.json()
} 