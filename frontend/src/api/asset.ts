import apiClient from './index'

const api = apiClient

export interface Asset {
  id: number
  name: string
  description: string | null
  asset_type: string
  file_url: string
  file_size: number | null
  mime_type: string | null
  tags: string[]
  community_id: number
  uploaded_by_user_id: number | null
  uploader_name: string | null
  created_at: string
  updated_at: string
}

export interface PaginatedAssets {
  items: Asset[]
  total: number
  page: number
  page_size: number
}

export interface AssetUpdate {
  name?: string
  description?: string | null
  asset_type?: string
  tags?: string[]
}

export const ASSET_TYPE_LABELS: Record<string, string> = {
  image: '图片/插图',
  icon: 'SVG/图标',
  brand_file: '品牌规范文件',
  template: '设计模板',
}

export const ASSET_TYPE_ACCEPT: Record<string, string> = {
  image: '.jpg,.jpeg,.png,.gif,.webp',
  icon: '.svg,.png',
  brand_file: '.pdf,.ai,.psd,.fig,.zip',
  template: '.pdf,.fig,.zip,.psd,.ai',
}

export const listAssets = (params?: {
  asset_type?: string
  keyword?: string
  tags?: string
  page?: number
  page_size?: number
}) => api.get<PaginatedAssets>('/assets/', { params })

export const uploadAsset = (formData: FormData) =>
  api.post<Asset>('/assets/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

export const getAsset = (id: number) => api.get<Asset>(`/assets/${id}`)

export const updateAsset = (id: number, data: AssetUpdate) =>
  api.put<Asset>(`/assets/${id}`, data)

export const deleteAsset = (id: number) => api.delete(`/assets/${id}`)

// Content ↔ Asset linking
export const listContentAssets = (contentId: number) =>
  api.get<Asset[]>(`/contents/${contentId}/assets`)

export const linkAssetToContent = (contentId: number, assetId: number) =>
  api.post<Asset>(`/contents/${contentId}/assets/${assetId}`)

export const unlinkAssetFromContent = (contentId: number, assetId: number) =>
  api.delete(`/contents/${contentId}/assets/${assetId}`)
