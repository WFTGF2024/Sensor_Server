<template>
  <nav class="navbar">
    <div class="container">
      <div class="nav-brand">
        <router-link to="/">Sensor Flask</router-link>
      </div>
      <div class="nav-menu">
        <router-link to="/public" class="nav-link public-files">公开文件</router-link>
        <template v-if="userStore.isLoggedIn">
          <router-link to="/dashboard" class="nav-link">仪表盘</router-link>
          <router-link to="/files" class="nav-link">文件管理</router-link>
          <router-link to="/membership" class="nav-link">会员中心</router-link>
          <router-link to="/profile" class="nav-link">个人资料</router-link>
          <a @click="handleLogout" class="nav-link logout">退出</a>
        </template>
        <template v-else>
          <router-link to="/login" class="nav-link">登录</router-link>
          <router-link to="/register" class="nav-link register">注册</router-link>
        </template>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessageBox } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await userStore.logout()
    router.push('/')
  } catch (error) {
    // 用户取消操作
  }
}
</script>

<style scoped>
.navbar {
  background-color: #2c3e50;
  color: white;
  padding: 1rem 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.navbar .container {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-brand a {
  color: white;
  text-decoration: none;
  font-size: 1.5rem;
  font-weight: bold;
}

.nav-menu {
  display: flex;
  gap: 1rem;
}

.nav-link {
  color: white;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  transition: background-color 0.3s;
  cursor: pointer;
}

.nav-link:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.nav-link.logout {
  background-color: #e74c3c;
}

.nav-link.logout:hover {
  background-color: #c0392b;
}

.nav-link.register {
  background-color: #27ae60;
}

.nav-link.register:hover {
  background-color: #219150;
}

.nav-link.public-files {
  background-color: #9b59b6;
}

.nav-link.public-files:hover {
  background-color: #8e44ad;
}
</style>
