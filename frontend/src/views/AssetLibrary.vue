<template>
  <div class="asset-library-page">
    <!-- Page header -->
    <div class="page-title-row">
      <div>
        <h2>素材库</h2>
        <p class="subtitle">集中管理品牌素材、图片、图标和设计模板</p>
      </div>
      <el-button type="primary" @click="openUploadDialog">
        <el-icon><Upload /></el-icon>
        上传素材
      </el-button>
    </div>

    <div class="main-layout">
      <!-- Left sidebar: type filter -->
      <div class="filter-sidebar section-card">
        <div class="filter-title">素材类型</div>
        <div
          class="filter-item"
          :class="{ active: selectedType === '' }"
          @click="setType('')"
        >
          全部素材
          <span class="count">{{ total }}</span>
        </div>
        <div
          v-for="(label, val) in ASSET_TYPE_LABELS"
          :key="val"
          class="filter-item"
          :class="{ active: selectedType === val }"
          @click="setType(val)"
        >
          <el-icon class="type-icon"><component :is="typeIcon(val)" /></el-icon>
          {{ label }}
        </div>

        <div class="filter-title" style="margin-top: 20px;">搜索</div>
        <el-input
          v-model="keyword"
          placeholder="搜索素材名称"
          clearable
          @input="debouncedFetch"
          @clear="fetchAssets"
        />
      </div>

      <!-- Right: asset grid -->
      <div class="asset-grid-area">
        <div v-if="loading" class="loading-area">
          <el-skeleton :rows="3" animated />
        </div>
        <div v-else-if="assets.length === 0" class="empty-area">
          <el-empty description="暂无素材，点击「上传素材」添加" />
        </div>
        <div v-else class="asset-grid">
          <div
            v-for="asset in assets"
            :key="asset.id"
            class="asset-card"
            @click="openDetail(asset)"
          >
            <!-- Preview area -->
            <div class="asset-preview">
              <img
                v-if="isImage(asset)"
                :src="asset.file_url"
                :alt="asset.name"
                class="preview-img"
              />
              <div v-else class="preview-icon">
                <el-icon :size="40"><component :is="typeIcon(asset.asset_type)" /></el-icon>
                <span class="file-ext">{{ fileExt(asset.file_url) }}</span>
              </div>
            </div>
            <!-- Info -->
            <div class="asset-info">
              <div class="asset-name" :title="asset.name">{{ asset.name }}</div>
              <div class="asset-meta">
                <span class="badge badge-blue">{{ ASSET_TYPE_LABELS[asset.asset_type] || asset.asset_type }}</span>
                <span class="file-size">{{ formatSize(asset.file_size) }}</span>
              </div>
              <div class="asset-tags" v-if="asset.tags?.length">
                <span v-for="tag in asset.tags.slice(0, 3)" :key="tag" class="tag">{{ tag }}</span>
              </div>
            </div>
            <!-- Actions -->
            <div class="asset-actions" @click.stop>
              <el-button size="small" link :href="asset.file_url" target="_blank" tag="a">
                下载
              </el-button>
              <el-button size="small" link @click="openEditDialog(asset)">编辑</el-button>
              <el-button size="small" link type="danger" @click="handleDelete(asset)">删除</el-button>
            </div>
          </div>
        </div>

        <!-- Pagination -->
        <div class="pagination-row" v-if="total > pageSize">
          <el-pagination
            v-model:current-page="currentPage"
            :page-size="pageSize"
            :total="total"
            layout="prev, pager, next"
            @current-change="fetchAssets"
          />
        </div>
      </div>
    </div>

    <!-- Upload dialog -->
    <el-dialog v-model="uploadDialogVisible" title="上传素材" width="500px" destroy-on-close>
      <el-form ref="uploadFormRef" :model="uploadForm" :rules="uploadRules" label-width="80px">
        <el-form-item label="素材名称" prop="name">
          <el-input v-model="uploadForm.name" placeholder="请输入素材名称" />
        </el-form-item>
        <el-form-item label="素材类型" prop="asset_type">
          <el-select v-model="uploadForm.asset_type" style="width: 100%" @change="uploadForm.file = null">
            <el-option v-for="(label, val) in ASSET_TYPE_LABELS" :key="val" :label="label" :value="val" />
          </el-select>
        </el-form-item>
        <el-form-item label="上传文件" prop="file">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :accept="currentAccept"
            :on-change="handleFileChange"
            :on-remove="() => { uploadForm.file = null }"
            drag
          >
            <el-icon class="upload-icon"><UploadFilled /></el-icon>
            <div class="upload-text">拖拽文件到此处或 <em>点击上传</em></div>
            <div class="upload-hint">支持：{{ currentAccept }}</div>
          </el-upload>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="uploadForm.description" type="textarea" :rows="2" placeholder="素材描述（可选）" />
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="uploadForm.tags" placeholder="多个标签用逗号分隔，如：品牌,logo,2024" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleUpload">上传</el-button>
      </template>
    </el-dialog>

    <!-- Edit dialog -->
    <el-dialog v-model="editDialogVisible" title="编辑素材信息" width="480px" destroy-on-close>
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="素材名称">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="素材类型">
          <el-select v-model="editForm.asset_type" style="width: 100%">
            <el-option v-for="(label, val) in ASSET_TYPE_LABELS" :key="val" :label="label" :value="val" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="editForm.tagsInput" placeholder="多个标签用逗号分隔" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="editSubmitting" @click="handleEditSubmit">保存</el-button>
      </template>
    </el-dialog>

    <!-- Detail drawer -->
    <el-drawer v-model="detailVisible" :title="detailAsset?.name" size="380px">
      <template v-if="detailAsset">
        <div class="detail-preview">
          <img v-if="isImage(detailAsset)" :src="detailAsset.file_url" class="detail-img" />
          <div v-else class="detail-file-icon">
            <el-icon :size="64"><component :is="typeIcon(detailAsset.asset_type)" /></el-icon>
            <div>{{ fileExt(detailAsset.file_url) }}</div>
          </div>
        </div>
        <el-descriptions :column="1" size="small" border style="margin-top: 16px">
          <el-descriptions-item label="类型">
            {{ ASSET_TYPE_LABELS[detailAsset.asset_type] || detailAsset.asset_type }}
          </el-descriptions-item>
          <el-descriptions-item label="文件大小">
            {{ formatSize(detailAsset.file_size) }}
          </el-descriptions-item>
          <el-descriptions-item label="上传者">
            {{ detailAsset.uploader_name || '—' }}
          </el-descriptions-item>
          <el-descriptions-item label="上传时间">
            {{ formatDateTime(detailAsset.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="标签">
            <div v-if="detailAsset.tags?.length">
              <span v-for="tag in detailAsset.tags" :key="tag" class="tag">{{ tag }}</span>
            </div>
            <span v-else class="text-muted">—</span>
          </el-descriptions-item>
          <el-descriptions-item v-if="detailAsset.description" label="描述">
            {{ detailAsset.description }}
          </el-descriptions-item>
        </el-descriptions>
        <div style="margin-top: 16px; text-align: center">
          <el-button type="primary" :href="detailAsset.file_url" target="_blank" tag="a">
            下载素材
          </el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ElMessage, ElMessageBox, type FormInstance, type FormRules, type UploadFile } from 'element-plus'
import { Picture, Folder, Document, Files, Upload, UploadFilled } from '@element-plus/icons-vue'
import { onMounted, reactive, ref, computed } from 'vue'
import {
  listAssets,
  uploadAsset,
  updateAsset,
  deleteAsset,
  ASSET_TYPE_LABELS,
  ASSET_TYPE_ACCEPT,
  type Asset,
} from '@/api/asset'

// ─── State ─────────────────────────────────────────────────────────────────
const loading = ref(false)
const uploading = ref(false)
const editSubmitting = ref(false)
const assets = ref<Asset[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20

const selectedType = ref('')
const keyword = ref('')

const uploadDialogVisible = ref(false)
const editDialogVisible = ref(false)
const detailVisible = ref(false)
const detailAsset = ref<Asset | null>(null)

const uploadFormRef = ref<FormInstance>()
const uploadRef = ref()

const uploadForm = reactive({
  name: '',
  asset_type: 'image',
  description: '',
  tags: '',
  file: null as File | null,
})

const uploadRules: FormRules = {
  name: [{ required: true, message: '请输入素材名称', trigger: 'blur' }],
  asset_type: [{ required: true, message: '请选择素材类型', trigger: 'change' }],
}

const editForm = reactive({
  id: 0,
  name: '',
  description: '',
  asset_type: 'image',
  tagsInput: '',
})

const currentAccept = computed(() => ASSET_TYPE_ACCEPT[uploadForm.asset_type] || '*')

// ─── Methods ────────────────────────────────────────────────────────────────
let fetchTimer: ReturnType<typeof setTimeout> | null = null
const debouncedFetch = () => {
  if (fetchTimer) clearTimeout(fetchTimer)
  fetchTimer = setTimeout(() => fetchAssets(), 400)
}

const fetchAssets = async () => {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      page: currentPage.value,
      page_size: pageSize,
    }
    if (selectedType.value) params.asset_type = selectedType.value
    if (keyword.value) params.keyword = keyword.value

    const resp = await listAssets(params)
    assets.value = resp.data.items
    total.value = resp.data.total
  } catch {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

const setType = (type: string) => {
  selectedType.value = type
  currentPage.value = 1
  fetchAssets()
}

const openUploadDialog = () => {
  Object.assign(uploadForm, { name: '', asset_type: 'image', description: '', tags: '', file: null })
  uploadDialogVisible.value = true
}

const handleFileChange = (file: UploadFile) => {
  uploadForm.file = file.raw || null
  if (!uploadForm.name && file.name) {
    uploadForm.name = file.name.replace(/\.[^.]+$/, '')
  }
}

const handleUpload = async () => {
  if (!uploadFormRef.value) return
  await uploadFormRef.value.validate()
  if (!uploadForm.file) {
    ElMessage.warning('请选择要上传的文件')
    return
  }
  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('file', uploadForm.file)
    fd.append('name', uploadForm.name)
    fd.append('asset_type', uploadForm.asset_type)
    if (uploadForm.description) fd.append('description', uploadForm.description)
    if (uploadForm.tags) fd.append('tags', uploadForm.tags)

    await uploadAsset(fd)
    ElMessage.success('素材已上传')
    uploadDialogVisible.value = false
    fetchAssets()
  } catch {
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
  }
}

const openDetail = (asset: Asset) => {
  detailAsset.value = asset
  detailVisible.value = true
}

const openEditDialog = (asset: Asset) => {
  Object.assign(editForm, {
    id: asset.id,
    name: asset.name,
    description: asset.description || '',
    asset_type: asset.asset_type,
    tagsInput: (asset.tags || []).join(', '),
  })
  editDialogVisible.value = true
}

const handleEditSubmit = async () => {
  editSubmitting.value = true
  try {
    const tags = editForm.tagsInput
      ? editForm.tagsInput.split(',').map((t) => t.trim()).filter(Boolean)
      : []
    await updateAsset(editForm.id, {
      name: editForm.name,
      description: editForm.description || null,
      asset_type: editForm.asset_type,
      tags,
    })
    ElMessage.success('已更新')
    editDialogVisible.value = false
    fetchAssets()
  } catch {
    ElMessage.error('更新失败')
  } finally {
    editSubmitting.value = false
  }
}

const handleDelete = async (asset: Asset) => {
  await ElMessageBox.confirm(`确认删除素材「${asset.name}」？此操作将同时删除文件。`, '删除确认', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning',
  })
  try {
    await deleteAsset(asset.id)
    ElMessage.success('已删除')
    fetchAssets()
  } catch {
    ElMessage.error('删除失败')
  }
}

const isImage = (asset: Asset) => {
  return asset.asset_type === 'image' || /\.(jpg|jpeg|png|gif|webp|svg)$/i.test(asset.file_url)
}

const typeIcon = (type: string) => {
  switch (type) {
    case 'image': return Picture
    case 'icon': return Files
    case 'brand_file': return Folder
    case 'template': return Document
    default: return Document
  }
}

const fileExt = (url: string) => {
  const m = url.match(/\.([^.?]+)(\?|$)/)
  return m ? m[1].toUpperCase() : 'FILE'
}

const formatSize = (bytes: number | null) => {
  if (!bytes) return '—'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

const formatDateTime = (dt: string) => {
  return new Date(dt).toLocaleString('zh-CN')
}

onMounted(fetchAssets)
</script>

<style scoped>
.asset-library-page {
  --text-primary:   #1e293b;
  --text-secondary: #64748b;
  --text-muted:     #94a3b8;
  --blue:           #0095ff;
  --border:         #e2e8f0;
  --shadow:         0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-hover:   0 4px 12px rgba(0, 0, 0, 0.08);
  --radius:         12px;

  padding: 32px 40px 60px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
}

.page-title-row h2 {
  margin: 0 0 6px;
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.subtitle {
  margin: 0;
  font-size: 15px;
  color: var(--text-secondary);
}

.main-layout {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.section-card {
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  transition: all 0.2s ease;
}

.filter-sidebar {
  width: 200px;
  flex-shrink: 0;
  padding: 20px 16px;
}

.filter-title {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--text-muted);
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.filter-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 2px;
  transition: background 0.15s;
  gap: 6px;
}

.filter-item:hover {
  background: #f8fafc;
  color: var(--text-primary);
}

.filter-item.active {
  background: #eff6ff;
  color: var(--blue);
  font-weight: 500;
}

.count {
  background: #f1f5f9;
  color: var(--text-muted);
  border-radius: 10px;
  padding: 0 6px;
  font-size: 11px;
}

.type-icon {
  margin-right: 2px;
}

.asset-grid-area {
  flex: 1;
  min-width: 0;
}

.asset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}

.asset-card {
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: var(--shadow);
  cursor: pointer;
  transition: box-shadow 0.2s ease;
  display: flex;
  flex-direction: column;
}

.asset-card:hover {
  box-shadow: var(--shadow-hover);
}

.asset-preview {
  height: 140px;
  background: #f8fafc;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.preview-icon {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  color: var(--text-muted);
}

.file-ext {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.asset-info {
  padding: 12px 14px 8px;
  flex: 1;
}

.asset-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 6px;
}

.asset-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.file-size {
  font-size: 12px;
  color: var(--text-muted);
}

.asset-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.tag {
  display: inline-block;
  padding: 1px 6px;
  background: #f1f5f9;
  color: var(--text-secondary);
  border-radius: 4px;
  font-size: 11px;
}

.asset-actions {
  padding: 8px 14px 12px;
  display: flex;
  gap: 4px;
  border-top: 1px solid #f1f5f9;
}

.badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 500;
}

.badge-blue { background: #eff6ff; color: #1d4ed8; }

.loading-area, .empty-area {
  padding: 60px 20px;
  text-align: center;
}

.pagination-row {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

.text-muted { color: var(--text-muted); }

.detail-preview {
  text-align: center;
  padding: 20px;
  background: #f8fafc;
  border-radius: 8px;
}

.detail-img {
  max-width: 100%;
  max-height: 240px;
  border-radius: 8px;
}

.detail-file-icon {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: var(--text-muted);
  padding: 20px 0;
}

:deep(.el-button) {
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.15s ease;
}

:deep(.el-button--primary) {
  background: var(--blue);
  border-color: var(--blue);
}

:deep(.el-button--primary:hover) {
  background: #0080e6;
  border-color: #0080e6;
}

:deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--border);
  border-radius: 8px;
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--blue), 0 0 0 3px rgba(0, 149, 255, 0.1);
}

:deep(.el-dialog) { border-radius: var(--radius); }
:deep(.el-dialog__header) { border-bottom: 1px solid #f1f5f9; }

:deep(.el-upload-dragger) {
  border-color: var(--border);
  border-radius: 8px;
  width: 100%;
}

:deep(.el-upload-dragger:hover) {
  border-color: var(--blue);
}

:deep(.el-pagination .el-pager li.is-active) {
  background: var(--blue);
  color: white;
}

.upload-icon {
  font-size: 48px;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.upload-text {
  font-size: 14px;
  color: var(--text-secondary);
}

.upload-text em {
  color: var(--blue);
  font-style: normal;
}

.upload-hint {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
}

@media (max-width: 1200px) {
  .asset-library-page { padding: 28px 24px; }
}

@media (max-width: 734px) {
  .asset-library-page { padding: 20px 16px; }
  .page-title-row h2 { font-size: 22px; }
  .page-title-row { flex-direction: column; align-items: flex-start; gap: 12px; }
  .main-layout { flex-direction: column; }
  .filter-sidebar { width: 100%; }
}
</style>
