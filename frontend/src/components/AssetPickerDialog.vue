<template>
  <el-dialog
    v-model="visible"
    title="从素材库选取"
    width="820px"
    :close-on-click-modal="false"
    class="asset-picker-dialog"
  >
    <!-- 搜索 + 类型筛选 -->
    <div class="picker-toolbar">
      <div class="type-tabs">
        <button
          v-for="tab in typeTabs"
          :key="tab.value"
          class="type-tab"
          :class="{ active: filterType === tab.value }"
          @click="filterType = tab.value; fetchAssets()"
        >{{ tab.label }}</button>
      </div>
      <el-input
        v-model="keyword"
        placeholder="搜索素材名称…"
        size="small"
        clearable
        style="width: 200px"
        @input="debouncedFetch"
        @clear="fetchAssets()"
      />
    </div>

    <!-- 素材网格 -->
    <div v-if="loading" class="picker-loading">
      <el-icon :size="28" class="spin"><Loading /></el-icon>
    </div>
    <div v-else-if="assets.length === 0" class="picker-empty">
      <el-icon :size="36"><PictureRounded /></el-icon>
      <p>素材库中暂无匹配素材</p>
    </div>
    <div v-else class="asset-grid">
      <div
        v-for="asset in assets"
        :key="asset.id"
        class="asset-card"
        :class="{ selected: selectedId === asset.id }"
        @click="selectedId = asset.id"
        @dblclick="handleConfirm"
      >
        <div class="asset-thumb">
          <img
            v-if="isImage(asset)"
            :src="asset.file_url"
            :alt="asset.name"
            class="thumb-img"
          />
          <div v-else class="thumb-icon">
            <el-icon :size="28"><Document /></el-icon>
            <span class="thumb-ext">{{ fileExt(asset.file_url) }}</span>
          </div>
        </div>
        <div class="asset-info">
          <div class="asset-name" :title="asset.name">{{ asset.name }}</div>
          <div class="asset-meta">
            <span class="type-badge" :class="typeBadgeClass(asset.asset_type)">
              {{ ASSET_TYPE_LABELS[asset.asset_type] || asset.asset_type }}
            </span>
            <span v-if="asset.file_size" class="asset-size">{{ formatSize(asset.file_size) }}</span>
          </div>
        </div>
        <div v-if="selectedId === asset.id" class="selected-check">
          <el-icon><Check /></el-icon>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="total > pageSize" class="picker-pagination">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        small
        @current-change="fetchAssets()"
      />
    </div>

    <template #footer>
      <div class="picker-footer">
        <span v-if="selectedAsset" class="selected-hint">
          已选：{{ selectedAsset.name }}
        </span>
        <span v-else class="selected-hint muted">点击选择素材，双击直接插入</span>
        <div class="footer-actions">
          <el-button @click="visible = false">取消</el-button>
          <el-button type="primary" :disabled="!selectedId" @click="handleConfirm">确认插入</el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, PictureRounded, Document, Check } from '@element-plus/icons-vue'
import { listAssets, ASSET_TYPE_LABELS, type Asset } from '../api/asset'

interface Props {
  modelValue: boolean
  /** 限制只显示某种类型（可选），如 'image'。不传则显示全部并允许切换 */
  initialType?: string
}

const props = withDefaults(defineProps<Props>(), {
  initialType: '',
})

const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void
  (e: 'select', asset: Asset): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

// ─── State ────────────────────────────────────────────────
const assets = ref<Asset[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 18
const keyword = ref('')
const filterType = ref(props.initialType)
const selectedId = ref<number | null>(null)
const loading = ref(false)

const typeTabs = [
  { label: '全部', value: '' },
  { label: '图片/插图', value: 'image' },
  { label: 'SVG/图标', value: 'icon' },
  { label: '品牌文件', value: 'brand_file' },
  { label: '设计模板', value: 'template' },
]

const selectedAsset = computed(() => assets.value.find((a) => a.id === selectedId.value) ?? null)

// ─── Data Fetch ───────────────────────────────────────────
async function fetchAssets() {
  loading.value = true
  selectedId.value = null
  try {
    const res = await listAssets({
      asset_type: filterType.value || undefined,
      keyword: keyword.value.trim() || undefined,
      page: page.value,
      page_size: pageSize,
    })
    assets.value = res.data.items
    total.value = res.data.total
  } catch {
    ElMessage.error('加载素材失败')
  } finally {
    loading.value = false
  }
}

let debounceTimer: ReturnType<typeof setTimeout> | null = null
function debouncedFetch() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    page.value = 1
    fetchAssets()
  }, 350)
}

// 打开时重置并拉数据
watch(visible, (open) => {
  if (open) {
    filterType.value = props.initialType
    keyword.value = ''
    page.value = 1
    selectedId.value = null
    fetchAssets()
  }
})

// ─── Actions ──────────────────────────────────────────────
function handleConfirm() {
  if (!selectedAsset.value) return
  emit('select', selectedAsset.value)
  visible.value = false
}

// ─── Helpers ──────────────────────────────────────────────
function isImage(asset: Asset): boolean {
  return asset.asset_type === 'image' || /\.(jpg|jpeg|png|gif|webp|svg)$/i.test(asset.file_url)
}

function fileExt(url: string): string {
  return url.split('.').pop()?.toUpperCase().slice(0, 5) ?? 'FILE'
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function typeBadgeClass(type: string): string {
  const map: Record<string, string> = {
    image: 'badge-blue',
    icon: 'badge-green',
    brand_file: 'badge-orange',
    template: 'badge-purple',
  }
  return map[type] ?? 'badge-gray'
}
</script>

<style scoped>
.picker-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.type-tabs {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.type-tab {
  padding: 4px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: #fff;
  font-size: 12px;
  font-weight: 500;
  color: #64748b;
  cursor: pointer;
  transition: all 0.15s;
}
.type-tab:hover { border-color: #cbd5e1; color: #1e293b; }
.type-tab.active { background: #eff6ff; border-color: #0095ff; color: #0095ff; }

/* ── Grid ── */
.asset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
  min-height: 240px;
  max-height: 440px;
  overflow-y: auto;
  padding: 2px;
}

.asset-card {
  position: relative;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.15s;
  background: #fff;
}
.asset-card:hover { border-color: #94a3b8; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
.asset-card.selected { border-color: #0095ff; box-shadow: 0 0 0 2px rgba(0,149,255,0.15); }

.asset-thumb {
  height: 110px;
  background: #f8fafc;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.thumb-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.thumb-icon {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  color: #94a3b8;
}
.thumb-ext {
  font-size: 10px;
  font-weight: 700;
  background: #f1f5f9;
  border-radius: 4px;
  padding: 2px 5px;
  color: #64748b;
}

.asset-info {
  padding: 8px 8px 6px;
}

.asset-name {
  font-size: 12px;
  font-weight: 500;
  color: #1e293b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
}

.asset-meta {
  display: flex;
  align-items: center;
  gap: 5px;
  flex-wrap: wrap;
}

.type-badge {
  font-size: 10px;
  font-weight: 500;
  padding: 2px 6px;
  border-radius: 4px;
}
.badge-blue   { background: #eff6ff; color: #1d4ed8; }
.badge-green  { background: #f0fdf4; color: #15803d; }
.badge-orange { background: #fffbeb; color: #b45309; }
.badge-purple { background: #fdf4ff; color: #7e22ce; }
.badge-gray   { background: #f1f5f9; color: #64748b; }

.asset-size {
  font-size: 10px;
  color: #94a3b8;
}

/* ── Selected check ── */
.selected-check {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 20px;
  height: 20px;
  background: #0095ff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 12px;
}

/* ── States ── */
.picker-loading,
.picker-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 240px;
  gap: 10px;
  color: #94a3b8;
}
.picker-empty p { font-size: 13px; margin: 0; }

.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Pagination ── */
.picker-pagination {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}

/* ── Footer ── */
.picker-footer {
  display: flex;
  align-items: center;
  gap: 12px;
}
.selected-hint {
  flex: 1;
  font-size: 13px;
  color: #1e293b;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.selected-hint.muted { color: #94a3b8; font-weight: 400; }
.footer-actions { display: flex; gap: 8px; flex-shrink: 0; }

/* ── Dialog overrides ── */
:deep(.el-dialog) { border-radius: 12px; }
:deep(.el-dialog__header) { border-bottom: 1px solid #f1f5f9; padding: 16px 20px; }
:deep(.el-dialog__body) { padding: 20px; }
:deep(.el-dialog__footer) { border-top: 1px solid #f1f5f9; padding: 12px 20px; }
:deep(.el-button) { border-radius: 8px; font-weight: 500; }
:deep(.el-button--primary:not(.is-link)) { background: #0095ff; border-color: #0095ff; }
:deep(.el-button--primary:not(.is-link):hover) { background: #0080e6; border-color: #0080e6; }
:deep(.el-input__wrapper) { box-shadow: 0 0 0 1px #e2e8f0; border-radius: 8px; }
:deep(.el-input__wrapper.is-focus) { box-shadow: 0 0 0 1px #0095ff, 0 0 0 3px rgba(0,149,255,0.1); }
:deep(.el-pagination .el-pager li.is-active) { background: #0095ff; color: #fff; }
</style>
