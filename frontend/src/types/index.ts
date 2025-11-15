export interface Memory {
  id: string
  content: string
  metadata?: Record<string, string>
  created_at: string
  updated_at: string
}

export interface MemoryCreate {
  content: string
  metadata?: Record<string, string>
}
