import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// 创建axios实例
const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  },
  withCredentials: true // 携带cookie
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    // 可以在这里添加token等
    // const token = localStorage.getItem('token')
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`
    // }
    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    const res = response.data

    // 如果返回的是文件流（下载）
    if (response.config.responseType === 'blob') {
      return response
    }

    // 统一处理响应
    if (res.success === false) {
      ElMessage.error(res.error?.message || '请求失败')
      return Promise.reject(new Error(res.error?.message || '请求失败'))
    }

    return res
  },
  (error) => {
    console.error('响应错误:', error)

    // 处理HTTP错误状态码
    if (error.response) {
      const { status, data } = error.response

      // 对于获取用户信息的401错误,不显示错误消息(静默失败)
      const isSilentFail = error.config?.silentFail === true

      switch (status) {
        case 401:
          if (!isSilentFail) {
            ElMessage.error('未授权，请重新登录')
            router.push('/login')
          }
          break
        case 403:
          if (!isSilentFail) {
            ElMessage.error('拒绝访问')
          }
          break
        case 404:
          if (!isSilentFail) {
            ElMessage.error('请求的资源不存在')
          }
          break
        case 500:
          if (!isSilentFail) {
            ElMessage.error('服务器错误')
          }
          break
        default:
          if (!isSilentFail) {
            ElMessage.error(data?.error?.message || '请求失败')
          }
      }
    } else if (error.request) {
      if (!error.config?.silentFail) {
        ElMessage.error('网络错误，请检查网络连接')
      }
    } else {
      if (!error.config?.silentFail) {
        ElMessage.error('请求配置错误')
      }
    }

    return Promise.reject(error)
  }
)

export default request
