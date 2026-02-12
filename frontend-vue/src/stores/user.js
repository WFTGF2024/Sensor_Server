import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, logout as logoutApi, getUserInfo } from '@/api'
import { ElMessage } from 'element-plus'

export const useUserStore = defineStore('user', () => {
  const userInfo = ref(null)
  const loading = ref(false)

  // 是否已登录
  const isLoggedIn = computed(() => {
    return !!userInfo.value
  })

  // 用户名
  const username = computed(() => {
    return userInfo.value?.username || ''
  })

  // 用户ID
  const userId = computed(() => {
    return userInfo.value?.user_id || null
  })

  /**
   * 用户登录
   */
  const login = async (credentials) => {
    loading.value = true
    try {
      await loginApi(credentials)
      // 登录成功后获取用户信息
      await fetchUserInfo()
      console.log('用户信息已获取:', userInfo.value)
      ElMessage.success('登录成功')
      return true
    } catch (error) {
      console.error('登录失败:', error)
      return false
    } finally {
      loading.value = false
    }
  }

  /**
   * 用户登出
   */
  const logout = async () => {
    loading.value = true
    try {
      await logoutApi()
      userInfo.value = null
      ElMessage.success('已成功退出登录')
      return true
    } catch (error) {
      console.error('登出失败:', error)
      // 即使登出失败，也清除本地用户信息
      userInfo.value = null
      return false
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取用户信息
   */
  const fetchUserInfo = async () => {
    loading.value = true
    try {
      const res = await getUserInfo()
      console.log('getUserInfo 响应:', res)
      // 后端返回格式: { success: true, user: {...} }
      userInfo.value = res.user || res.data || res
      console.log('设置 userInfo:', userInfo.value)
      return userInfo.value
    } catch (error) {
      console.error('获取用户信息失败:', error)
      userInfo.value = null
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 更新用户信息
   */
  const updateUserInfo = (newUserInfo) => {
    userInfo.value = { ...userInfo.value, ...newUserInfo }
  }

  return {
    userInfo,
    loading,
    isLoggedIn,
    username,
    userId,
    login,
    logout,
    fetchUserInfo,
    updateUserInfo
  }
})
