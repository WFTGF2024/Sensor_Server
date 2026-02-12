import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getFileList, uploadFile, deleteFile, updateFile } from '@/api'
import { ElMessage } from 'element-plus'

export const useFileStore = defineStore('file', () => {
  const files = ref([])
  const loading = ref(false)
  const uploadProgress = ref(0)

  /**
   * 获取文件列表
   */
  const fetchFiles = async () => {
    loading.value = true
    try {
      const res = await getFileList()
      // 后端直接返回数组，所以直接使用 res
      files.value = Array.isArray(res) ? res : (res.data || [])
      return files.value
    } catch (error) {
      console.error('获取文件列表失败:', error)
      ElMessage.error('获取文件列表失败')
      return []
    } finally {
      loading.value = false
    }
  }

  /**
   * 上传文件
   */
  const upload = async (fileData, onProgress) => {
    loading.value = true
    uploadProgress.value = 0
    try {
      const res = await uploadFile(fileData, (progressEvent) => {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        )
        uploadProgress.value = percentCompleted
        if (onProgress) {
          onProgress(percentCompleted)
        }
      })
      ElMessage.success('文件上传成功')
      await fetchFiles() // 刷新文件列表
      return res.data
    } catch (error) {
      console.error('文件上传失败:', error)
      ElMessage.error('文件上传失败')
      throw error
    } finally {
      loading.value = false
      uploadProgress.value = 0
    }
  }

  /**
   * 删除文件
   */
  const deleteFileById = async (fileId) => {
    try {
      await deleteFile(fileId)
      ElMessage.success('文件删除成功')
      // 从列表中移除
      files.value = files.value.filter((file) => file.file_id !== fileId)
      return true
    } catch (error) {
      console.error('文件删除失败:', error)
      ElMessage.error('文件删除失败')
      return false
    }
  }

  /**
   * 更新文件信息
   */
  const updateFileById = async (fileId, data) => {
    try {
      await updateFile(fileId, data)
      ElMessage.success('文件信息更新成功')
      // 更新列表中的文件信息
      const index = files.value.findIndex((file) => file.file_id === fileId)
      if (index !== -1) {
        files.value[index] = { ...files.value[index], ...data }
      }
      return true
    } catch (error) {
      console.error('文件信息更新失败:', error)
      ElMessage.error('文件信息更新失败')
      return false
    }
  }

  /**
   * 清空文件列表
   */
  const clearFiles = () => {
    files.value = []
  }

  return {
    files,
    loading,
    uploadProgress,
    fetchFiles,
    upload,
    deleteFileById,
    updateFileById,
    clearFiles
  }
})
