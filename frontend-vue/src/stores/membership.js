import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getMembershipInfo, getMembershipLevels, upgradeMembership } from '@/api'
import { ElMessage } from 'element-plus'

export const useMembershipStore = defineStore('membership', () => {
  const membership = ref(null)
  const levels = ref([])
  const loading = ref(false)

  // 当前会员等级代码
  const levelCode = computed(() => {
    return membership.value?.level_code || 'free'
  })

  // 当前会员等级名称
  const levelName = computed(() => {
    return membership.value?.level_name || '普通用户'
  })

  // 存储使用情况
  const storageUsed = computed(() => {
    return membership.value?.storage_used || 0
  })

  // 存储限额
  const storageLimit = computed(() => {
    return membership.value?.storage_limit || 0
  })

  // 存储使用百分比
  const storagePercentage = computed(() => {
    if (storageLimit.value === 0) return 0
    return Math.round((storageUsed.value / storageLimit.value) * 100 * 100) / 100
  })

  /**
   * 获取会员信息
   */
  const fetchMembershipInfo = async () => {
    loading.value = true
    try {
      const res = await getMembershipInfo()
      // 后端返回格式: { success: true, membership: {...} }
      membership.value = res.membership || res.data || res
      return res.membership || res.data || res
    } catch (error) {
      console.error('获取会员信息失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取所有会员等级
   */
  const fetchMembershipLevels = async () => {
    loading.value = true
    try {
      const res = await getMembershipLevels()
      levels.value = res.data || []
      return levels.value
    } catch (error) {
      console.error('获取会员等级失败:', error)
      ElMessage.error('获取会员等级失败')
      return []
    } finally {
      loading.value = false
    }
  }

  /**
   * 升级会员
   */
  const upgrade = async (levelId) => {
    loading.value = true
    try {
      await upgradeMembership({ level_id: levelId })
      ElMessage.success('会员升级成功')
      await fetchMembershipInfo() // 刷新会员信息
      return true
    } catch (error) {
      console.error('会员升级失败:', error)
      ElMessage.error('会员升级失败')
      return false
    } finally {
      loading.value = false
    }
  }

  return {
    membership,
    levels,
    loading,
    levelCode,
    levelName,
    storageUsed,
    storageLimit,
    storagePercentage,
    fetchMembershipInfo,
    fetchMembershipLevels,
    upgrade
  }
})
