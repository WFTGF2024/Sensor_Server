import request from '@/utils/request'

/**
 * 获取会员信息
 */
export const getMembershipInfo = () => {
  return request({
    url: '/membership/info',
    method: 'get'
  })
}

/**
 * 获取所有会员等级
 */
export const getMembershipLevels = () => {
  return request({
    url: '/membership/levels',
    method: 'get'
  })
}

/**
 * 升级会员
 */
export const upgradeMembership = (data) => {
  return request({
    url: '/membership/upgrade',
    method: 'post',
    data
  })
}

/**
 * 获取会员权益
 */
export const getMembershipBenefits = () => {
  return request({
    url: '/membership/benefits',
    method: 'get'
  })
}

/**
 * 获取会员操作日志
 */
export const getMembershipLogs = (params) => {
  return request({
    url: '/membership/logs',
    method: 'get',
    params
  })
}
