<template>
  <div class="container">
    <div class="card" style="text-align: center; padding: 4rem 2rem;">
      <div class="card-body">
        <h1 style="font-size: 3rem; margin-bottom: 1rem; color: #2c3e50;">
          欢迎使用 Sensor Flask
        </h1>
        <p style="font-size: 1.25rem; color: #6c757d; margin-bottom: 2rem;">
          安全、可靠的文件存储和管理服务
        </p>

        <div class="d-flex justify-content-center gap-3" style="flex-wrap: wrap;">
          <template v-if="!userStore.isLoggedIn">
            <router-link to="/login">
              <el-button type="primary" size="large">立即登录</el-button>
            </router-link>
            <router-link to="/register">
              <el-button type="success" size="large">免费注册</el-button>
            </router-link>
          </template>
        </div>
      </div>
    </div>

    <div class="stats-grid mt-4">
      <div class="stat-card">
        <div class="stat-value" style="color: #3498db;">安全</div>
        <div class="stat-label">数据加密存储</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color: #27ae60;">快速</div>
        <div class="stat-label">高速上传下载</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color: #f39c12;">灵活</div>
        <div class="stat-label">多种会员方案</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color: #9b59b6;">便捷</div>
        <div class="stat-label">简单易用界面</div>
      </div>
    </div>

    <div class="card mt-4">
      <div class="card-header text-center">
        <h2 class="card-title">会员等级</h2>
      </div>
      <div class="card-body">
        <div class="stats-grid">
          <div class="stat-card">
            <h3>
              <el-tag type="info" size="large">普通用户</el-tag>
            </h3>
            <p class="mt-2"><strong>存储容量：</strong> 1GB</p>
            <p><strong>单文件大小：</strong> 50MB</p>
            <p><strong>文件数量：</strong> 100个</p>
            <p class="text-muted mt-2">基础文件存储</p>
          </div>
          <div class="stat-card">
            <h3>
              <el-tag size="large">白银会员</el-tag>
            </h3>
            <p class="mt-2"><strong>存储容量：</strong> 5GB</p>
            <p><strong>单文件大小：</strong> 100MB</p>
            <p><strong>文件数量：</strong> 500个</p>
            <p class="text-muted mt-2">文件分享功能</p>
          </div>
          <div class="stat-card">
            <h3>
              <el-tag type="warning" size="large">黄金会员</el-tag>
            </h3>
            <p class="mt-2"><strong>存储容量：</strong> 10GB</p>
            <p><strong>单文件大小：</strong> 200MB</p>
            <p><strong>文件数量：</strong> 1000个</p>
            <p class="text-muted mt-2">公开链接、每日下载100次</p>
          </div>
          <div class="stat-card">
            <h3>
              <el-tag type="danger" size="large">钻石会员</el-tag>
            </h3>
            <p class="mt-2"><strong>存储容量：</strong> 50GB</p>
            <p><strong>单文件大小：</strong> 1GB</p>
            <p><strong>文件数量：</strong> 10000个</p>
            <p class="text-muted mt-2">每日下载1000次、每日上传500次</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

onMounted(async () => {
  // 尝试获取用户信息(静默失败,不提示错误)
  try {
    await userStore.fetchUserInfo()
  } catch (error) {
    // 未登录或其他错误,静默失败
    // 不输出日志,避免控制台显示401错误
  }
})
</script>

<style scoped>
.card-body {
  padding: 2rem;
}

.mt-2 {
  margin-top: 0.5rem;
}

.mt-4 {
  margin-top: 2rem;
}

.text-muted {
  color: #6c757d;
}
</style>
