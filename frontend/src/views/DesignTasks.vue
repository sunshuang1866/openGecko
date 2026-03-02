<template>
  <div class="design-tasks-page">
    <!-- Page header -->
    <div class="page-title-row">
      <div>
        <h2>设计任务</h2>
        <p class="subtitle">管理设计工作安排，跟踪设计产出的进度</p>
      </div>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>
        新建任务
      </el-button>
    </div>

    <!-- Filters -->
    <div class="section-card filter-card">
      <el-row :gutter="12">
        <el-col :span="5">
          <el-select v-model="filters.status" placeholder="按状态筛选" clearable @change="fetchTasks">
            <el-option v-for="(label, val) in TASK_STATUS_LABELS" :key="val" :label="label" :value="val" />
          </el-select>
        </el-col>
        <el-col :span="5">
          <el-select v-model="filters.task_type" placeholder="按类型筛选" clearable @change="fetchTasks">
            <el-option v-for="(label, val) in TASK_TYPE_LABELS" :key="val" :label="label" :value="val" />
          </el-select>
        </el-col>
        <el-col :span="5">
          <el-select v-model="filters.priority" placeholder="按优先级筛选" clearable @change="fetchTasks">
            <el-option v-for="(label, val) in TASK_PRIORITY_LABELS" :key="val" :label="label" :value="val" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-button @click="resetFilters">重置</el-button>
        </el-col>
      </el-row>
    </div>

    <!-- Table -->
    <div class="section-card">
      <el-table
        v-loading="loading"
        :data="tasks"
        style="width: 100%"
        row-key="id"
      >
        <el-table-column prop="title" label="任务标题" min-width="180">
          <template #default="{ row }">
            <span class="task-title">{{ row.title }}</span>
          </template>
        </el-table-column>
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <span class="badge badge-blue">{{ TASK_TYPE_LABELS[row.task_type] || row.task_type }}</span>
          </template>
        </el-table-column>
        <el-table-column label="优先级" width="90">
          <template #default="{ row }">
            <span :class="['badge', priorityBadgeClass(row.priority)]">
              {{ TASK_PRIORITY_LABELS[row.priority] || row.priority }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-select
              v-model="row.status"
              size="small"
              style="width: 110px"
              @change="(val: string) => handleStatusChange(row, val)"
            >
              <el-option v-for="(label, val) in TASK_STATUS_LABELS" :key="val" :label="label" :value="val" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="责任人" width="120">
          <template #default="{ row }">
            <span v-if="row.assignee_name" class="assignee-name">{{ row.assignee_name }}</span>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="截止日期" width="120">
          <template #default="{ row }">
            <span v-if="row.due_date" :class="{ 'overdue': isOverdue(row.due_date) }">
              {{ formatDate(row.due_date) }}
            </span>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="关联内容" min-width="140">
          <template #default="{ row }">
            <span v-if="row.content_title" class="content-link">{{ row.content_title }}</span>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="openEditDialog(row)">编辑</el-button>
            <el-button size="small" type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="pagination-row" v-if="total > pageSize">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          @current-change="fetchTasks"
        />
      </div>
    </div>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingTask ? '编辑设计任务' : '新建设计任务'"
      width="560px"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="任务标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入任务标题" />
        </el-form-item>
        <el-form-item label="任务类型" prop="task_type">
          <el-select v-model="form.task_type" style="width: 100%">
            <el-option v-for="(label, val) in TASK_TYPE_LABELS" :key="val" :label="label" :value="val" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="form.priority" style="width: 100%">
            <el-option v-for="(label, val) in TASK_PRIORITY_LABELS" :key="val" :label="label" :value="val" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="editingTask" label="状态">
          <el-select v-model="form.status" style="width: 100%">
            <el-option v-for="(label, val) in TASK_STATUS_LABELS" :key="val" :label="label" :value="val" />
          </el-select>
        </el-form-item>
        <el-form-item label="责任人">
          <el-select v-model="form.assignee_id" placeholder="选择责任人（可选）" clearable style="width: 100%">
            <el-option
              v-for="member in communityMembers"
              :key="member.id"
              :label="member.full_name || member.username"
              :value="member.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="截止日期">
          <el-date-picker
            v-model="form.due_date"
            type="date"
            placeholder="选择截止日期（可选）"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="任务描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="详细说明任务内容（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ editingTask ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { onMounted, reactive, ref } from 'vue'
import {
  createDesignTask,
  deleteDesignTask,
  listDesignTasks,
  TASK_PRIORITY_LABELS,
  TASK_STATUS_LABELS,
  TASK_TYPE_LABELS,
  updateDesignTask,
  updateDesignTaskStatus,
  type DesignTask,
  type DesignTaskListItem,
} from '@/api/design'
import apiClient from '@/api/index'
import { useCommunityStore } from '@/stores/community'

// ─── State ─────────────────────────────────────────────────────────────────
const communityStore = useCommunityStore()
const loading = ref(false)
const submitting = ref(false)
const tasks = ref<DesignTaskListItem[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20

const filters = reactive({
  status: '',
  task_type: '',
  priority: '',
})

const dialogVisible = ref(false)
const editingTask = ref<DesignTaskListItem | null>(null)
const formRef = ref<FormInstance>()

const form = reactive({
  title: '',
  description: '',
  task_type: 'other',
  status: 'not_started',
  priority: 'medium',
  assignee_id: null as number | null,
  due_date: null as string | null,
})

const rules: FormRules = {
  title: [{ required: true, message: '请输入任务标题', trigger: 'blur' }],
  task_type: [{ required: true, message: '请选择任务类型', trigger: 'change' }],
}

const communityMembers = ref<{ id: number; username: string; full_name: string | null }[]>([])

// ─── Methods ────────────────────────────────────────────────────────────────
const fetchTasks = async () => {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      page: currentPage.value,
      page_size: pageSize,
    }
    if (filters.status) params.status = filters.status
    if (filters.task_type) params.task_type = filters.task_type
    if (filters.priority) params.priority = filters.priority

    const resp = await listDesignTasks(params)
    tasks.value = resp.data.items
    total.value = resp.data.total
  } catch {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

const fetchMembers = async () => {
  const communityId = communityStore.currentCommunityId
  if (!communityId) return
  try {
    const resp = await apiClient.get(`/communities/${communityId}/users`)
    communityMembers.value = resp.data?.items || resp.data || []
  } catch {
    // ignore
  }
}

const resetFilters = () => {
  filters.status = ''
  filters.task_type = ''
  filters.priority = ''
  currentPage.value = 1
  fetchTasks()
}

const openCreateDialog = () => {
  editingTask.value = null
  Object.assign(form, {
    title: '',
    description: '',
    task_type: 'other',
    status: 'not_started',
    priority: 'medium',
    assignee_id: null,
    due_date: null,
  })
  dialogVisible.value = true
}

const openEditDialog = (task: DesignTaskListItem) => {
  editingTask.value = task
  Object.assign(form, {
    title: task.title,
    description: '',
    task_type: task.task_type,
    status: task.status,
    priority: task.priority,
    assignee_id: task.assignee_id,
    due_date: task.due_date,
  })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  submitting.value = true
  try {
    if (editingTask.value) {
      await updateDesignTask(editingTask.value.id, {
        title: form.title,
        description: form.description || null,
        task_type: form.task_type,
        status: form.status,
        priority: form.priority,
        assignee_id: form.assignee_id,
        due_date: form.due_date,
      })
      ElMessage.success('任务已更新')
    } else {
      await createDesignTask({
        title: form.title,
        description: form.description || null,
        task_type: form.task_type,
        priority: form.priority,
        assignee_id: form.assignee_id,
        due_date: form.due_date,
      })
      ElMessage.success('任务已创建')
    }
    dialogVisible.value = false
    fetchTasks()
  } catch {
    ElMessage.error('操作失败')
  } finally {
    submitting.value = false
  }
}

const handleStatusChange = async (task: DesignTaskListItem, status: string) => {
  try {
    await updateDesignTaskStatus(task.id, status)
    task.status = status
    ElMessage.success('状态已更新')
  } catch {
    ElMessage.error('状态更新失败')
    fetchTasks() // revert
  }
}

const handleDelete = async (task: DesignTaskListItem) => {
  await ElMessageBox.confirm(`确认删除任务「${task.title}」？`, '删除确认', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning',
  })
  try {
    await deleteDesignTask(task.id)
    ElMessage.success('已删除')
    fetchTasks()
  } catch {
    ElMessage.error('删除失败')
  }
}

const priorityBadgeClass = (priority: string) => {
  if (priority === 'high') return 'badge-red'
  if (priority === 'medium') return 'badge-orange'
  return 'badge-gray'
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleDateString('zh-CN')
}

const isOverdue = (date: string) => {
  return new Date(date) < new Date() && true
}

onMounted(() => {
  fetchTasks()
  fetchMembers()
})
</script>

<style scoped>
.design-tasks-page {
  --text-primary:   #1e293b;
  --text-secondary: #64748b;
  --text-muted:     #94a3b8;
  --blue:           #0095ff;
  --green:          #22c55e;
  --orange:         #f59e0b;
  --red:            #ef4444;
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

.section-card {
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px 28px;
  margin-bottom: 24px;
  box-shadow: var(--shadow);
  transition: all 0.2s ease;
}

.filter-card {
  padding: 16px 24px;
}

.badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.badge-blue   { background: #eff6ff; color: #1d4ed8; }
.badge-green  { background: #f0fdf4; color: #15803d; }
.badge-orange { background: #fffbeb; color: #b45309; }
.badge-red    { background: #fef2f2; color: #dc2626; }
.badge-gray   { background: #f1f5f9; color: #64748b; }

.task-title {
  font-weight: 500;
  color: var(--text-primary);
}

.assignee-name {
  color: var(--text-secondary);
  font-size: 14px;
}

.content-link {
  color: var(--blue);
  font-size: 13px;
}

.text-muted {
  color: var(--text-muted);
}

.overdue {
  color: var(--red);
  font-weight: 500;
}

.pagination-row {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

:deep(.el-button) {
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.15s ease;
}

:deep(.el-button--primary:not(.is-link)) {
  background: var(--blue);
  border-color: var(--blue);
}

:deep(.el-button--primary:not(.is-link):hover) {
  background: #0080e6;
  border-color: #0080e6;
}

:deep(.el-table th) {
  background: #f8fafc;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--border);
}

:deep(.el-table td) {
  border-bottom: 1px solid #f1f5f9;
}

:deep(.el-table .el-table__row:hover > td) {
  background: #f8fafc !important;
}

:deep(.el-dialog) {
  border-radius: var(--radius);
}

:deep(.el-dialog__header) {
  border-bottom: 1px solid #f1f5f9;
}

:deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--border);
  border-radius: 8px;
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--blue), 0 0 0 3px rgba(0, 149, 255, 0.1);
}

:deep(.el-pagination .el-pager li.is-active) {
  background: var(--blue);
  color: white;
}

@media (max-width: 1200px) {
  .design-tasks-page { padding: 28px 24px; }
}

@media (max-width: 734px) {
  .design-tasks-page { padding: 20px 16px; }
  .page-title-row h2 { font-size: 22px; }
  .section-card { padding: 16px; }
  .page-title-row { flex-direction: column; align-items: flex-start; gap: 12px; }
}
</style>
