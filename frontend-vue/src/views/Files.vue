<template>
  <div class="container">
    <div class="card">
      <div class="card-header">
        <h1 class="card-title">文件管理</h1>
        <el-button type="primary" :icon="Upload" @click="showUploadDialog = true">
          上传文件
        </el-button>
      </div>
      <div class="card-body">
        <!-- 存储使用情况 -->
        <div class="mb-4">
          <StorageProgress :used="storageUsed" :limit="storageLimit" />
        </div>

        <!-- 文件列表 -->
        <el-table :data="files" v-loading="loading" stripe style="width: 100%">
          <el-table-column prop="file_name" label="文件名" min-width="200" />
          <el-table-column label="文件大小" width="120">
            <template #default="{ row }">
              {{ formatBytes(row.file_size) }}
            </template>
          </el-table-column>
          <el-table-column label="权限" width="100">
            <template #default="{ row }">
              <el-tag :type="row.file_permission === 'public' ? 'success' : 'info'" size="small">
                {{ row.file_permission === 'public' ? '公开' : '私有' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="上传时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link :icon="Download" @click="handleDownload(row)">
                下载
              </el-button>
              <el-button type="warning" link :icon="Edit" @click="handleEdit(row)">
                编辑
              </el-button>
              <el-button type="danger" link :icon="Delete" @click="handleDelete(row)">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-empty v-if="!loading && files.length === 0" description="暂无文件" />
      </div>
    </div>

    <!-- 上传文件对话框 -->
    <el-dialog v-model="showUploadDialog" title="上传文件" width="500px">
      <el-form :model="uploadForm" label-width="80px">
        <el-form-item label="选择文件">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :on-change="handleFileChange"
            :limit="1"
            :on-exceed="handleExceed"
          >
            <el-button type="primary">选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">
                单文件最大 {{ formatBytes(maxFileSize) }}
              </div>
            </template>
          </el-upload>
        </el-form-item>
        <el-form-item label="文件权限">
          <el-radio-group v-model="uploadForm.file_permission">
            <el-radio label="private">私有</el-radio>
            <el-radio label="public">公开</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="uploadForm.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleUpload">
          上传
        </el-button>
      </template>
    </el-dialog>

    <!-- 编辑文件对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑文件" width="500px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="文件名">
          <el-input v-model="editForm.file_name" disabled />
        </el-form-item>
        <el-form-item label="文件权限">
          <el-radio-group v-model="editForm.file_permission">
            <el-radio label="private">私有</el-radio>
            <el-radio label="public">公开</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="handleUpdateFile">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessageBox } from 'element-plus'
import { Upload, Download, Edit, Delete } from '@element-plus/icons-vue'
import { useFileStore } from '@/stores/file'
import { useMembershipStore } from '@/stores/membership'
import { downloadFile } from '@/api'
import StorageProgress from '@/components/StorageProgress.vue'

const fileStore = useFileStore()
const membershipStore = useMembershipStore()

const files = computed(() => fileStore.files)
const loading = computed(() => fileStore.loading)
const uploading = computed(() => fileStore.loading)
const uploadProgress = computed(() => fileStore.uploadProgress)

const showUploadDialog = ref(false)
const showEditDialog = ref(false)
const uploadRef = ref(null)

const uploadForm = ref({
  file: null,
  file_permission: 'private',
  description: ''
})

const editForm = ref({
  file_id: null,
  file_name: '',
  file_permission: 'private',
  description: ''
})

const storageUsed = computed(() => membershipStore.storageUsed)
const storageLimit = computed(() => membershipStore.storageLimit)
const maxFileSize = computed(() => membershipStore.membership?.max_file_size || 0)

const formatBytes = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

const handleFileChange = (file) => {
  uploadForm.value.file = file.raw
}

const handleExceed = () => {
  ElMessageBox.alert('只能上传一个文件，请先删除已选择的文件', '提示', {
    type: 'warning'
  })
}

const handleUpload = async () => {
  if (!uploadForm.value.file) {
    ElMessageBox.alert('请选择文件', '提示', { type: 'warning' })
    return
  }

  try {
    const formData = new FormData()
    formData.append('file', uploadForm.value.file)
    formData.append('file_permission', uploadForm.value.file_permission)
    formData.append('description', uploadForm.value.description)

    await fileStore.upload(formData, (progress) => {
      console.log('上传进度:', progress)
    })

    showUploadDialog.value = false
    uploadForm.value = {
      file: null,
      file_permission: 'private',
      description: ''
    }
    if (uploadRef.value) {
      uploadRef.value.clearFiles()
    }
  } catch (error) {
    console.error('上传失败:', error)
  }
}

const handleDownload = async (file) => {
  try {
    const response = await downloadFile(file.file_id)
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', file.file_name)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('下载失败:', error)
  }
}

const handleEdit = (file) => {
  editForm.value = {
    file_id: file.file_id,
    file_name: file.file_name,
    file_permission: file.file_permission,
    description: file.description || ''
  }
  showEditDialog.value = true
}

const handleUpdateFile = async () => {
  try {
    await fileStore.updateFileById(editForm.value.file_id, {
      file_permission: editForm.value.file_permission,
      description: editForm.value.description
    })
    showEditDialog.value = false
  } catch (error) {
    console.error('更新失败:', error)
  }
}

const handleDelete = async (file) => {
  try {
    await ElMessageBox.confirm(`确定要删除文件 "${file.file_name}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await fileStore.deleteFileById(file.file_id)
  } catch (error) {
    console.error('删除失败:', error)
  }
}

const loadData = async () => {
  try {
    await fileStore.fetchFiles()
    await membershipStore.fetchMembershipInfo()
  } catch (error) {
    console.error('加载数据失败:', error)
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-body {
  padding: 2rem;
}
</style>
