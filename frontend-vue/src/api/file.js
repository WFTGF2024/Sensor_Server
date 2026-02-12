import request from '@/utils/request'

/**
 * 上传文件
 */
export const uploadFile = (data) => {
  return request({
    url: '/download/upload',
    method: 'post',
    data,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 下载文件
 */
export const downloadFile = (fileId) => {
  return request({
    url: `/download/download/${fileId}`,
    method: 'get',
    responseType: 'blob'
  })
}

/**
 * 获取文件列表
 */
export const getFileList = () => {
  return request({
    url: '/download/files',
    method: 'get'
  })
}

/**
 * 获取公开文件列表
 */
export const getPublicFiles = () => {
  return request({
    url: '/download/public',
    method: 'get'
  })
}

/**
 * 获取文件详情
 */
export const getFileDetail = (fileId) => {
  return request({
    url: `/download/file/${fileId}`,
    method: 'get'
  })
}

/**
 * 更新文件信息
 */
export const updateFile = (fileId, data) => {
  return request({
    url: `/download/file/${fileId}`,
    method: 'put',
    data
  })
}

/**
 * 删除文件
 */
export const deleteFile = (fileId) => {
  return request({
    url: `/download/file/${fileId}`,
    method: 'delete'
  })
}
