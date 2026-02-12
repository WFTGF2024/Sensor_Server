<template>
  <div class="container">
    <div class="card">
      <div class="card-header">
        <h1 class="card-title">欢迎回来，{{ userStore.username }}！</h1>
      </div>
      <div class="card-body">
        <div class="stats-grid">
          <StatCard :value="filesCount" label="文件总数" />
          <StatCard :value="formatBytes(storageUsed)" label="已用存储" />
          <StatCard :value="formatBytes(storageLimit)" label="存储限额" />
          <StatCard :value="usagePercentage" label="使用率" suffix="%" />
        </div>

        <div class="card mt-4">
          <div class="card-header">
            <h2 class="card-title">存储使用情况</h2>
          </div>
          <div class="card-body">
            <StorageProgress :used="storageUsed" :limit="storageLimit" />
          </div>
        </div>

        <div class="card mt-4">
          <div class="card-header">
            <h2 class="card-title">会员信息</h2>
          </div>
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-center">
              <div>
                <h3>
                  <el-tag :type="membershipTagType" size="large">
                    {{ membershipStore.levelName }}
                  </el-tag>
                </h3>
                <p class="text-muted mt-2">单文件最大：{{ formatBytes(maxFileSize) }}</p>
                <p class="text-muted">文件数量限制：{{ maxFileCount }} 个</p>
              </div>
              <el-button type="primary" @click="$router.push('/membership')">
                升级会员
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { useFileStore } from '@/stores/file'
import { useMembershipStore } from '@/stores/membership'
import StatCard from '@/components/StatCard.vue'
import StorageProgress from '@/components/StorageProgress.vue'

const userStore = useUserStore()
const fileStore = useFileStore()
const membershipStore = useMembershipStore()

const filesCount = ref(0)
const storageUsed = ref(0)
const storageLimit = ref(0)
const usagePercentage = ref(0)
const maxFileSize = ref(0)
const maxFileCount = ref(0)

const membershipTagType = computed(() => {
  const typeMap = {
    free: 'info',
    silver: '',
    gold: 'warning',
    diamond: 'danger'
  }
  return typeMap[membershipStore.levelCode] || 'info'
})

const formatBytes = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

const loadData = async () => {
  try {
    // 获取文件列表
    const files = await fileStore.fetchFiles()
    filesCount.value = files.length

    // 获取会员信息
    await membershipStore.fetchMembershipInfo()
    storageUsed.value = membershipStore.storageUsed
    storageLimit.value = membershipStore.storageLimit
    usagePercentage.value = membershipStore.storagePercentage

    if (membershipStore.membership) {
      maxFileSize.value = membershipStore.membership.max_file_size || 0
      maxFileCount.value = membershipStore.membership.max_file_count || 0
    }
  } catch (error) {
    console.error('加载数据失败:', error)
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.card-body {
  padding: 2rem;
}
</style>
