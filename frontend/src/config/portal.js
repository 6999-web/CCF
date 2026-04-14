export const roleConfig = {
  child: {
    title: '儿童端',
    subtitle: '趣味训练与游戏数据采集',
    accent: 'blue',
    menu: [
      { key: 'overview', label: '概览' },
      { key: 'levels', label: '关卡' },
      { key: 'reports', label: '报告' },
      { key: 'rewards', label: '奖励' },
      { key: 'profile', label: '个人资料' },
    ],
  },
  parent: {
    title: '家长端',
    subtitle: '筛查报告、问卷、AI 问答与预约',
    accent: 'pink',
    menu: [
      { key: 'overview', label: '概览' },
      { key: 'children', label: '儿童档案' },
      { key: 'reports', label: '报告' },
      { key: 'chat', label: 'AI 问答' },
      { key: 'appointments', label: '预约' },
      { key: 'profile', label: '个人资料' },
    ],
  },
  counselor: {
    title: '咨询师端',
    subtitle: '订单、排班、干预计划与知识库',
    accent: 'green',
    menu: [
      { key: 'overview', label: '概览' },
      { key: 'orders', label: '订单' },
      { key: 'plans', label: '干预方案' },
      { key: 'knowledge', label: '知识库' },
      { key: 'profile', label: '个人资料' },
    ],
  },
  management: {
    title: '管理端',
    subtitle: '用户、内容、配置、审计与看板',
    accent: 'orange',
    menu: [
      { key: 'overview', label: '概览' },
      { key: 'users', label: '用户' },
      { key: 'content', label: '内容' },
      { key: 'settings', label: '配置' },
      { key: 'logs', label: '审计' },
      { key: 'profile', label: '个人资料' },
    ],
  },
  teacher_research: {
    title: '教研室端',
    subtitle: '自评、材料与整改闭环',
    accent: 'indigo',
    menu: [
      { key: 'overview', label: '概览' },
      { key: 'self', label: '自评' },
      { key: 'materials', label: '材料' },
      { key: 'followup', label: '整改' },
      { key: 'profile', label: '个人资料' },
    ],
  },
}

export const managementRoles = [
  { value: 'review_group', label: '评教小组' },
  { value: 'review_office', label: '评教小组办公室' },
  { value: 'academic_affairs', label: '教务处' },
]
