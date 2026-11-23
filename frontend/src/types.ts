export type Role = 'admin' | 'editor' | 'viewer'

export interface User {
  id: number
  email: string
  full_name: string
}

export interface Workspace {
  id: number
  name: string
  description: string
  my_role: Role
  created_at: string
}

export interface Member {
  user_id: number
  email: string
  full_name: string
  role: Role
}

export interface DocumentItem {
  id: number
  workspace_id: number
  filename: string
  status: 'pending' | 'processing' | 'ready' | 'error'
  pages: number
  error_message: string
  created_at: string
}

export interface Citation {
  index: number
  document_id: number
  filename: string
  page: number
  excerpt: string
}

export interface ChatMessage {
  id?: number
  role: 'user' | 'assistant'
  content: string
  citations: Citation[]
}

export interface Conversation {
  id: number
  title: string
  created_at: string
}

export const ROLE_LABELS: Record<Role, string> = {
  admin: 'Administrateur',
  editor: 'Éditeur',
  viewer: 'Lecteur',
}
