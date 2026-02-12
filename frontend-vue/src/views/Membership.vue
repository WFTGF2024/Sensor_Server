<template>
  <div class="container">
    <div class="card">
      <div class="card-header">
        <h1 class="card-title">会员中心</h1>
      </div>
      <div class="card-body">
        <!-- 当前会员信息 -->
        <div class="card mb-4">
          <div class="card-header">
            <h2 class="card-title">当前会员</h2>
          </div>
          <div class="card-body">
            <div class="stats-grid">
              <StatCard :value="membershipStore.levelName" label="会员等级" />
              <StatCard :value="formatBytes(storageUsed)" label="已用存储" />
              <StatCard :value="formatBytes(storageLimit)" label="存储限额" />
              <StatCard :value="usagePercentage" label="使用率" suffix="%" />
            </div>
            <div class="mt-4">
              <StorageProgress :used="storageUsed" :limit="storageLimit" />
            </div>
            <div class="mt-4">
              <h3>会员特权</h3>
              <el-tag
                v-for="privilege in privileges"
                :key="privilege"
                class="mr-2 mt-2"
                type="success"
              >
                {{ privilege }}
              </el-tag>
            </div>
          </div>
        </div>

        <!-- 可升级会员等级 -->
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">升级会员</h2>
          </div>
          <div class="card-body">
            <div class="stats-grid">
              <div
                v-for="level in availableLevels"
                :key="level.level_code"
                class="stat-card"
                :class="{ 'current-level': level.level_code === membershipStore.levelCode }"
              >
                <h3>
                  <el-tag :type="getLevelTagType(level.level_code)" size="large">
                    {{ level.level_name }}
                  </el-tag>
                </h3>
                <p class="mt-2"><strong>存储容量：</strong> {{ formatBytes(level.storage_limit) }}</p>
                <p><strong>单文件大小：</strong> {{ formatBytes(level.max_file_size) }}</p>
                <p><strong>文件数量：</strong> {{ level.max_file_count }} 个</p>
                <el-button
                  v-if="level.level_code !== membershipStore.levelCode"
                  type="primary"
                  class="mt-3"
                  :loading="loading && upgradingLevel === level.level_id"
                  @click="handleUpgrade(level)"
                >
                  升级
                </el-button>
                <el-tag v-else type="info" class="mt-3">当前等级</el-tag>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessageBox } from 'element-plus'
import { useMembershipStore } from '@/stores/membership'
import StatCard from '@/components/StatCard.vue'
import StorageProgress from '@/components/StorageProgress.vue'

const membershipStore = useMembershipStore()

const availableLevels = ref([])
const loading = ref(false)
const upgradingLevel = ref(null)

const storageUsed = computed(() => membershipStore.storageUsed)
const storageLimit = computed(() => membershipStore.storageLimit)
const usagePercentage = computed(() => membershipStore.storagePercentage)

const privileges = computed(() => {
  const level = membershipStore.levelCode
  const privilegeMap = {
    free: ['基础文件存储'],
    silver: ['基础文件存储', '文件分享功能'],
    gold: ['基础文件存储', '文件分享功能', '公开链接', '每日下载100次'],
    diamond: [
      '基础文件存储',
      '文件分享功能',
      '公开链接',
      '每日下载1000次',
      '每日上传500次'
    ]
  }
  return privilegeMap[level] || []
})

const formatBytes = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

const getLevelTagType = (levelCode) => {
  const typeMap = {
    free: 'info',
    silver: '',
    gold: 'warning',
    diamond: 'danger'
  }
  return typeMap[levelCode] || 'info'
}

const handleUpgrade = async (level) => {
  try {
    await ElMessageBox.confirm(
      `确定要升级到 ${level.level_name} 吗？`,
      '确认升级',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    loading.value = true
    upgradingLevel.value = level.level_id

    const success = await membershipStore.upgrade(level.level_id)

    if (success) {
      await loadData()
    }
  } catch (error) {
    console.error('升级失败:', error)
  } finally {
    loading.value = false
    upgradingLevel.value = null
  }
}

const loadData = async () => {
  try {
    await membershipStore.fetchMembershipInfo()
    availableLevels.value = await membershipStore.fetchMembershipLevels()
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

.stat-card {
  cursor: pointer;
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.current-level {
  border: 2px solid #3498db;
}

.mr-2 {
  margin-right: 0.5rem;
}

.mt-2 {
  margin-top: 0.5rem;
}

.mt-3 {
  margin-top: 1rem;
}

.mt-4 {
  margin-top: 1.5rem;
}

.mb-4 {
  margin-bottom: 1.5rem;
}
</style>
