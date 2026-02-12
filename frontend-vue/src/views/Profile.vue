<template>
  <div class="container">
    <div class="card">
      <div class="card-header">
        <h1 class="card-title">个人资料</h1>
      </div>
      <div class="card-body">
        <el-tabs v-model="activeTab">
          <!-- 基本信息 -->
          <el-tab-pane label="基本信息" name="info">
            <el-form :model="profileForm" :rules="profileRules" ref="profileRef" label-width="100px">
              <el-form-item label="用户名">
                <el-input v-model="profileForm.username" disabled />
              </el-form-item>
              <el-form-item label="邮箱" prop="email">
                <el-input v-model="profileForm.email" placeholder="请输入邮箱" />
              </el-form-item>
              <el-form-item label="手机号" prop="phone">
                <el-input v-model="profileForm.phone" placeholder="请输入手机号" />
              </el-form-item>
              <el-form-item label="QQ号">
                <el-input v-model="profileForm.qq" placeholder="请输入QQ号" />
              </el-form-item>
              <el-form-item label="微信号">
                <el-input v-model="profileForm.wechat" placeholder="请输入微信号" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="loading" @click="handleUpdateProfile">
                  保存
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <!-- 修改密码 -->
          <el-tab-pane label="修改密码" name="password">
            <el-form
              :model="passwordForm"
              :rules="passwordRules"
              ref="passwordRef"
              label-width="100px"
            >
              <el-form-item label="当前密码" prop="oldPassword">
                <el-input
                  v-model="passwordForm.oldPassword"
                  type="password"
                  placeholder="请输入当前密码"
                  show-password
                />
              </el-form-item>
              <el-form-item label="新密码" prop="newPassword">
                <el-input
                  v-model="passwordForm.newPassword"
                  type="password"
                  placeholder="请输入新密码"
                  show-password
                />
              </el-form-item>
              <el-form-item label="确认密码" prop="confirmPassword">
                <el-input
                  v-model="passwordForm.confirmPassword"
                  type="password"
                  placeholder="请确认新密码"
                  show-password
                />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="loading" @click="handleChangePassword">
                  修改密码
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <!-- 账户设置 -->
          <el-tab-pane label="账户设置" name="settings">
            <el-alert
              title="危险操作"
              type="error"
              description="删除账户是不可逆的操作，删除后您的所有数据将被永久删除。"
              :closable="false"
              show-icon
              class="mb-4"
            />
            <el-button type="danger" @click="handleDeleteAccount">删除账户</el-button>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { updateUserInfo, changePassword, deleteAccount } from '@/api'

const userStore = useUserStore()

const activeTab = ref('info')
const loading = ref(false)

const profileRef = ref(null)
const passwordRef = ref(null)

const profileForm = reactive({
  username: '',
  email: '',
  phone: '',
  qq: '',
  wechat: ''
})

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const profileRules = {
  email: [{ type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }],
  phone: [{ pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }]
}

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== passwordForm.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  oldPassword: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少 6 个字符', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (!/[A-Z]/.test(value)) {
          callback(new Error('密码必须包含至少一个大写字母'))
        } else if (!/[a-z]/.test(value)) {
          callback(new Error('密码必须包含至少一个小写字母'))
        } else if (!/\d/.test(value)) {
          callback(new Error('密码必须包含至少一个数字'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const loadUserInfo = () => {
  if (userStore.userInfo) {
    profileForm.username = userStore.userInfo.username || ''
    profileForm.email = userStore.userInfo.email || ''
    profileForm.phone = userStore.userInfo.phone || ''
    profileForm.qq = userStore.userInfo.qq || ''
    profileForm.wechat = userStore.userInfo.wechat || ''
  }
}

const handleUpdateProfile = async () => {
  if (!profileRef.value) return

  await profileRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await updateUserInfo({
          email: profileForm.email,
          phone: profileForm.phone,
          qq: profileForm.qq,
          wechat: profileForm.wechat
        })
        // 更新本地用户信息
        userStore.updateUserInfo({
          email: profileForm.email,
          phone: profileForm.phone,
          qq: profileForm.qq,
          wechat: profileForm.wechat
        })
        ElMessageBox.alert('个人信息更新成功', '提示', { type: 'success' })
      } catch (error) {
        console.error('更新失败:', error)
      } finally {
        loading.value = false
      }
    }
  })
}

const handleChangePassword = async () => {
  if (!passwordRef.value) return

  await passwordRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await changePassword({
          old_password: passwordForm.oldPassword,
          new_password: passwordForm.newPassword
        })
        // 清空表单
        passwordForm.oldPassword = ''
        passwordForm.newPassword = ''
        passwordForm.confirmPassword = ''
        ElMessageBox.alert('密码修改成功，请重新登录', '提示', { type: 'success' })
        // 登出
        await userStore.logout()
        window.location.href = '/login'
      } catch (error) {
        console.error('修改密码失败:', error)
      } finally {
        loading.value = false
      }
    }
  })
}

const handleDeleteAccount = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要删除账户吗？此操作不可撤销，所有数据将被永久删除。',
      '危险操作',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'error',
        confirmButtonClass: 'el-button--danger'
      }
    )

    await deleteAccount()
    ElMessageBox.alert('账户已删除', '提示', { type: 'success' })
    // 清空用户信息并跳转到首页
    userStore.logout()
    window.location.href = '/'
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除账户失败:', error)
    }
  }
}

onMounted(() => {
  loadUserInfo()
})
</script>

<style scoped>
.card-body {
  padding: 2rem;
}

.mb-4 {
  margin-bottom: 1.5rem;
}
</style>
