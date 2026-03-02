import apiClient from './index'

const api = apiClient

export interface DesignTask {
  id: number
  title: string
  description: string | null
  task_type: string
  status: string
  priority: string
  assignee_id: number | null
  assignee_name: string | null
  due_date: string | null
  community_id: number
  created_by_user_id: number | null
  content_id: number | null
  content_title: string | null
  created_at: string
  updated_at: string
}

export interface DesignTaskListItem {
  id: number
  title: string
  task_type: string
  status: string
  priority: string
  assignee_id: number | null
  assignee_name: string | null
  due_date: string | null
  content_id: number | null
  content_title: string | null
  created_at: string
  updated_at: string
}

export interface PaginatedDesignTasks {
  items: DesignTaskListItem[]
  total: number
  page: number
  page_size: number
}

export interface DesignTaskCreate {
  title: string
  description?: string | null
  task_type?: string
  priority?: string
  assignee_id?: number | null
  due_date?: string | null
  content_id?: number | null
}

export interface DesignTaskUpdate {
  title?: string
  description?: string | null
  task_type?: string
  status?: string
  priority?: string
  assignee_id?: number | null
  due_date?: string | null
  content_id?: number | null
}

export const TASK_TYPE_LABELS: Record<string, string> = {
  poster: '海报',
  icon: '图标',
  illustration: '插图',
  logo: 'Logo',
  template: '模板',
  brand_guide: '品牌规范',
  other: '其他',
}

export const TASK_STATUS_LABELS: Record<string, string> = {
  not_started: '未开始',
  in_progress: '进行中',
  review: '待审核',
  completed: '已完成',
}

export const TASK_PRIORITY_LABELS: Record<string, string> = {
  low: '低',
  medium: '中',
  high: '高',
}

export const listDesignTasks = (params?: {
  status?: string
  task_type?: string
  priority?: string
  assignee_id?: number
  page?: number
  page_size?: number
}) => api.get<PaginatedDesignTasks>('/design-tasks/', { params })

export const createDesignTask = (data: DesignTaskCreate) =>
  api.post<DesignTask>('/design-tasks/', data)

export const getDesignTask = (id: number) =>
  api.get<DesignTask>(`/design-tasks/${id}`)

export const updateDesignTask = (id: number, data: DesignTaskUpdate) =>
  api.put<DesignTask>(`/design-tasks/${id}`, data)

export const updateDesignTaskStatus = (id: number, status: string) =>
  api.patch<DesignTask>(`/design-tasks/${id}/status`, { status })

export const deleteDesignTask = (id: number) =>
  api.delete(`/design-tasks/${id}`)
