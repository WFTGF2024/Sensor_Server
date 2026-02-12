<template>
  <div class="container">
    <div class="card" style="max-width: 400px; margin: 2rem auto;">
      <div class="card-header">
        <h2 class="card-title text-center">登录</h2>
      </div>
      <div class="card-body">
        <el-form :model="form" :rules="rules" ref="formRef" @submit.prevent="handleLogin">
          <el-form-item prop="username">
            <el-input
              v-model="form.username"
              placeholder="用户名"
              size="large"
              :prefix-icon="User"
            />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="密码"
              size="large"
              :prefix-icon="Lock"
              show-password
            />
          </el-form-item>
          <el-form-item>
            <el-button
              type="primary"
              size="large"
              :loading="loading"
              @click="handleLogin"
              style="width: 100%"
            >
              登录
            </el-button>
          </el-form-item>
        </el-form>
        <div class="text-center mt-2">
          <router-link to="/register">还没有账号？立即注册</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { User, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少 6 个字符', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const success = await userStore.login(form)
        if (success) {
          // 等待一小段时间确保用户信息已经更新
          await new Promise(resolve => setTimeout(resolve, 100))
          // 跳转到重定向页面或文件管理页面
          const redirect = route.query.redirect || '/files'
          console.log('登录成功，准备跳转到:', redirect)
          console.log('当前登录状态:', userStore.isLoggedIn)
          router.push(redirect)
        }
      } catch (error) {
        console.error('登录过程出错:', error)
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.card-body {
  padding: 2rem;
}

.text-center a {
  color: #3498db;
  text-decoration: none;
}

.text-center a:hover {
  text-decoration: underline;
}
</style>
