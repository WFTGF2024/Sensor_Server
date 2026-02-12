import request from '@/utils/request'

/**
 * 用户注册
 */
export const register = (data) => {
  return request({
    url: '/auth/register',
    method: 'post',
    data
  })
}

/**
 * 用户登录
 */
export const login = (data) => {
  return request({
    url: '/auth/login',
    method: 'post',
    data
  })
}

/**
 * 用户登出
 */
export const logout = () => {
  return request({
    url: '/auth/logout',
    method: 'post'
  })
}

/**
 * 获取用户信息
 */
export const getUserInfo = () => {
  return request({
    url: '/auth/user',
    method: 'get',
    silentFail: true // 静默失败,不显示错误消息
  })
}

/**
 * 更新用户信息
 */
export const updateUserInfo = (data) => {
  return request({
    url: '/auth/user',
    method: 'put',
    data
  })
}

/**
 * 修改密码
 */
export const changePassword = (data) => {
  return request({
    url: '/auth/password',
    method: 'put',
    data
  })
}

/**
 * 删除账户
 */
export const deleteAccount = () => {
  return request({
    url: '/auth/account',
    method: 'delete'
  })
}
