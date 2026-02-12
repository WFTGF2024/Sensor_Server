<template>
  <div class="container">
    <div class="card">
      <div class="card-header">
        <h1 class="card-title">公开文件</h1>
        <el-tag type="success">无需登录即可浏览</el-tag>
      </div>
      <div class="card-body">
        <!-- 文件列表 -->
        <el-table :data="files" v-loading="loading" stripe style="width: 100%">
          <el-table-column prop="file_name" label="文件名" min-width="200" />
          <el-table-column label="上传者" width="120">
            <template #default="{ row }">
              {{ row.username }}
            </template>
          </el-table-column>
          <el-table-column label="文件大小" width="120">
            <template #default="{ row }">
              {{ formatBytes(row.file_size) }}
            </template>
          </el-table-column>
          <el-table-column label="描述" min-width="200">
            <template #default="{ row }">
              {{ row.description || '-' }}
            </template>
          </el-table-column>
          <el-table-column label="上传时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.updated_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link :icon="Download" @click="handleDownload(row)">
                下载
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-empty v-if="!loading && files.length === 0" description="暂无公开文件" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Download } from '@element-plus/icons-vue'
import { getPublicFiles, downloadFile } from '@/api'

const files = ref([])
const loading = ref(false)

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

const loadPublicFiles = async () => {
  loading.value = true
  try {
    const res = await getPublicFiles()
    // 后端直接返回数组，所以直接使用 res
    files.value = Array.isArray(res) ? res : (res.data || [])
  } catch (error) {
    console.error('获取公开文件列表失败:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadPublicFiles()
})
</script>

<style scoped>
.card-body {
  padding: 2rem;
}
</style>
